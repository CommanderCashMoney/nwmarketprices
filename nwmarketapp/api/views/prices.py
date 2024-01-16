import json
import logging
import pytz
from time import perf_counter
from dateutil.parser import isoparse

from django.core.handlers.wsgi import WSGIRequest
from django.db import connection
from django.db.models import Count
from django.http import FileResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view
from django.db.models import Subquery, OuterRef
from nwmarket.settings import CACHE_ENABLED
from nwmarketapp.api.utils import get_popular_items_dict_v2
from nwmarketapp.models import PriceSummary, Run, ConfirmedNames, Price, Servers




@ratelimit(key='ip', rate='4/s', block=True)
@cache_page(60 * 10)
def get_item_data(request: WSGIRequest, server_id: int, item_id) -> JsonResponse:

    if not item_id.isnumeric():
        # nwdb id was passed instead. COnvert this to my ids
        confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
        confirmed_names = confirmed_names.values_list('name', 'id', 'nwdb_id')
        try:
            item_id = confirmed_names.get(nwdb_id=item_id.lower())[1]
        except ConfirmedNames.DoesNotExist:
            return JsonResponse({"status": "Item name not found in database"}, status=404)
    try:
        ps = PriceSummary.objects.get(server_id=server_id, confirmed_name_id=item_id)
    except (PriceSummary.DoesNotExist):
        return JsonResponse({"status": "No prices found for this item."}, status=404)

    cn_id = request.GET.get("cn_id")
    # Single item request from /0/[server_id]/?cn_id=[item_id]
    # This is used by some of the price overlay tools
    if cn_id:
        json_data = {
            "recent_lowest_price": ps.recent_lowest_price['price'],
            "last_checked": isoparse(ps.recent_lowest_price['datetime']),
            "price_graph_data": ps.ordered_graph_data[-15:],
            "price_change": ps.price_change,
            "detail_view": sorted(ps.lowest_prices, key=lambda obj: obj["price"]),
            'item_name': ps.confirmed_name.name,
            'nwdb_id': ps.confirmed_name.nwdb_id
        }
    else:
        json_data = {
                "item_name": ps.confirmed_name.name,
                "item_id": ps.confirmed_name.id,
                "price_datetime": ps.recent_price_time,
                "graph_data": ps.ordered_graph_data[-15:],
                "detail_view": sorted(ps.lowest_prices, key=lambda obj: obj["price"]),
                "lowest_price": render_to_string("snippets/lowest-price.html", {
                    "recent_lowest_price": ps.recent_lowest_price['price'],
                    "highest_buy_order": ps.recent_lowest_price.get('buy_order_price', None),
                    "highest_buy_order_qty": ps.recent_lowest_price.get('qty', None),
                    "last_checked": isoparse(ps.recent_lowest_price['datetime']),
                    "price_change": ps.price_change,
                    "price_change_date": ps.price_change_date,
                    "detail_view": sorted(ps.lowest_prices, key=lambda obj: obj["price"]),
                    'item_name': ps.confirmed_name.name,
                    'nwdb_id': ps.confirmed_name.nwdb_id
                })}

    return JsonResponse(json_data, safe=False)



@cache_page(60 * 10)
def initial_page_load_data(request: WSGIRequest, server_id: int) -> JsonResponse:
    p = perf_counter()
    most_listed_item_top10 = []
    with connection.cursor() as cursor:
        cursor.callproc('most_comp_top9', [server_id])
        for row in cursor.fetchall():
            most_listed_item_top10.append((row[0], row[1], row[2]))




    popular_items = get_popular_items_dict_v2(server_id)
    popular_item_name_map = {
        "popular_endgame_data": "Popular End Game Items",
        "popular_base_data": "Popular Base Materials",
        "mote_data": "Motes",
        "refining_data": "Refining Reagents",
        "trophy_data": "Trophy Materials",
        "craft_mods": "Craft Mods",
        "coatings": "Coatings",
        "foods": "Foods"
    }

    popular_rendered = {
        popular_item_name_map[k].replace(" ", "-").lower(): render_to_string(
            "snippets/endgame_data_block2.html", context={
            "name": popular_item_name_map[k],
            "items": v
        })
        for k, v in popular_items.items()
    }
    return JsonResponse({
        "most_listed": list(most_listed_item_top10),
        "fetch_time": perf_counter() - p,
        **popular_rendered
    })

# Not rated limited because request to this are redirected to CloudFront
def latest_prices(request: WSGIRequest, server_id: int) -> FileResponse:
    p = perf_counter()
    final_prices = []
    try:
        ps = PriceSummary.objects.filter(server_id=server_id).select_related('confirmed_name')
        ps_values = list(ps.values_list('confirmed_name__nwdb_id', 'confirmed_name__name', 'lowest_prices').order_by('confirmed_name__name'))

    except (PriceSummary.DoesNotExist):
        json_data = {'status': 'not found'}
        return FileResponse(
            json.dumps(json_data, default=str),
            as_attachment=True,
            content_type='application/json',
            filename='nwmarketprices.json'
        )

    for item in ps_values:
        lowest10_prices = sorted(list(item[2]), key=lambda d: d['price'])
        if lowest10_prices[0]['price'] < 30:
            lowest10_prices = PriceSummary.filter_price_ouliers(lowest10_prices)

        final_prices.append([item[0], item[1], lowest10_prices[0]])


    items = [
        {
            "ItemId": row[0],
            "ItemName": row[1],
            "Price": f"{row[2]['price']}",
            "Availability": row[2]['avail'],
            "LastUpdated": row[2]['datetime'],
            "HighestBuyOrder": row[2].get('buy_order_price', None),
            "Qty": row[2].get('qty', None)
        } for row in final_prices
    ]
    t = perf_counter() - p
    print('latest-prices response time:', t)
    return FileResponse(
        json.dumps(items, default=str),
        as_attachment=True,
        content_type='application/json',
        filename='nwmarketprices.json'
    )



@api_view(['GET'])
@ratelimit(key='ip', rate='1/m', block=True)
def update_server_prices(request: WSGIRequest, server_id: int) -> JsonResponse:

    p = perf_counter()
    scanner_group = request.user.groups.filter(name="scanner_user")
    if not scanner_group.exists():
        return JsonResponse({"status": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    query = render_to_string("queries/get_item_data_full.sql", context={"server_id": server_id})
    with connection.cursor() as cursor:
        cursor.execute(query)

    return JsonResponse({"status": "ok", "calc_time": perf_counter() - p}, status=status.HTTP_201_CREATED)

@ratelimit(key='ip', rate='1/s', block=True)
@cache_page(60 * 5)
def server_scan_times(request: WSGIRequest) -> JsonResponse:
    runs = Run.objects.filter(server_id=OuterRef('id')).order_by('-id')
    servers = Servers.objects.annotate(rundate=Subquery(runs.values('start_date')[:1]))
    servers = servers.annotate(runtz=Subquery(runs.values('tz_name')[:1]))
    server_list = list(servers.values_list('id', 'name', 'rundate', 'runtz'))
    for idx, item in enumerate(server_list):
        if item[2] and item[3]:
            tz = pytz.timezone(item[3])
            utc_time = tz.normalize(tz.localize(item[2])).astimezone(pytz.utc)
            server_list[idx] = (item[0], item[1], utc_time)
        else:
            server_list[idx] = (item[0], item[1], item[2])


    return JsonResponse({"server_last_updated": server_list})
