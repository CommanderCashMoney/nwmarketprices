from dataclasses import dataclass
import json
import logging
from time import perf_counter

from django.core.handlers.wsgi import WSGIRequest
from django.db import connection
from django.db.models import Count
from django.http import FileResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view

from nwmarket.settings import CACHE_ENABLED
from nwmarketapp.api.utils import get_popular_items_dict, get_popular_items_dict_v2, get_price_graph_data, \
    get_list_by_nameid
from nwmarketapp.models import Craft, PriceSummary, Run, NWDBLookup, ConfirmedNames, Price


def get_item_data_v1(request: WSGIRequest, server_id: int, item_id: str) -> JsonResponse:
    p = perf_counter()
    empty_response = JsonResponse({
        "recent_lowest_price": 'N/A',
        "price_change": 'Not Found',
        "last_checked": 'Not Found'
    }, status=200)
    if not item_id.isnumeric():
        # nwdb id was passed instead. COnvert this to my ids
        confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
        confirmed_names = confirmed_names.values_list('name', 'id', 'nwdb_id')
        try:
            item_id = confirmed_names.get(nwdb_id=item_id.lower())[1]
        except ConfirmedNames.DoesNotExist:
            return empty_response

    item_data = get_list_by_nameid(item_id, server_id)
    if item_data is None:
        return empty_response
    grouped_hist = item_data["grouped_hist"]
    item_name = item_data["item_name"]
    if not grouped_hist:
        # we didnt find any prices with that name id
        return empty_response

    price_graph_data, avg_price_graph, num_listings = get_price_graph_data(grouped_hist)
    # convert to old style
    price_graph_data = [[price_dict["datetime"], price_dict["price"]] for price_dict in price_graph_data]

    try:
        nwdb_id = NWDBLookup.objects.get(name=item_data["item_name"])
        nwdb_id = nwdb_id.item_id
    except NWDBLookup.DoesNotExist:
        nwdb_id = ''

    return JsonResponse({
        "recent_lowest_price": item_data["recent_lowest_price"],
        "last_checked": item_data["recent_price_time"],
        "price_graph_data": price_graph_data,
        "price_change": item_data["price_change_text"],
        "avg_graph_data": avg_price_graph,
        "detail_view": item_data["lowest_10_raw"],
        'item_name': item_name,
        'num_listings': num_listings,
        'nwdb_id': nwdb_id,
        'calculation_time': perf_counter() - p
    }, status=200)

def testaa(data):
    res = []
    for dat in data:
        res.append({
            "name": dat.component.name,
            "quantity": dat.quantity
        })
    return res

@cache_page(60 * 10)
def get_item_data(request: WSGIRequest, server_id: int, item_id: int) -> JsonResponse:
    try:
        ps = PriceSummary.objects.get(server_id=server_id, confirmed_name_id=item_id)
        test = testaa(Craft.objects.filter(item_id=item_id))
        logging.basicConfig(level=logging.DEBUG)
        logging.debug(test)
    except Craft.DoesNotExist:
        return JsonResponse({"status": "not found"}, status=404)
    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "not found"}, status=404)
    return JsonResponse(
        {
            "item_name": ps.confirmed_name.name,
            "item_id": ps.confirmed_name.id,
            "price_datetime": ps.recent_price_time,
            "graph_data": ps.ordered_graph_data[-15:],
            # "detail_view": sorted(ps.lowest_prices, key=lambda obj: obj["price"]),
            "detail_view": test,
            "lowest_price": render_to_string("snippets/lowest-price.html", {
                "recent_lowest_price": ps.recent_lowest_price,
                "components": test,
                "last_checked": ps.recent_price_time,
                "price_change": ps.price_change,
                "price_change_date": ps.price_change_date,
                "detail_view": sorted(ps.lowest_prices, key=lambda obj: obj["price"]),
                'item_name': ps.confirmed_name.name,
                'nwdb_id': ps.confirmed_name.nwdb_id
            })
        }, safe=False)


@cache_page(60 * 10)
def intial_page_load_data(request: WSGIRequest, server_id: int) -> JsonResponse:
    p = perf_counter()
    try:
        last_run = Run.objects.filter(server_id=server_id, approved=True).latest("id")
        most_listed_item_top10 = Price.objects.filter(
            run=last_run,
            server_id=server_id
        ).values_list(
            'name',
        ).annotate(
            count=Count('price', distinct=True)
        ).values_list("name", "count").order_by("-count")[:9]
    except Run.DoesNotExist:
        most_listed_item_top10 = []


    popular_items = get_popular_items_dict_v2(server_id)
    popular_item_name_map = {
        "popular_endgame_data": "Popular End Game Items",
        "popular_base_data": "Popular Base Materials",
        "mote_data": "Motes",
        "refining_data": "Refining Reagents",
        "trophy_data": "Trophy Materials"
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


@ratelimit(key='ip', rate='1/s', block=True)
@cache_page(60 * 10)
def latest_prices(request: WSGIRequest, server_id: int) -> FileResponse:
    last_run = Run.objects.filter(server_id=server_id, approved=True).exclude(username="january").latest('id').start_date
    with connection.cursor() as cursor:
        query = f"""
        SELECT  max(rs.nwdb_id),rs.name, trunc(avg(rs.price)::numeric,2), max(rs.avail), max(rs.timestamp)
        FROM (
            SELECT p.price,p.name,p.timestamp,cn.nwdb_id,p.avail, Rank()
              over (Partition BY p.name_id ORDER BY price asc ) AS Rank
            FROM prices p
            join confirmed_names cn on p.name = cn.name
            where p.timestamp >= '{last_run}'
            and server_id = {server_id}
            and p.approved = true
        ) rs WHERE Rank <= 5
        group by rs.name
        order by rs.name;
        """
        cursor.execute(query)
        data = cursor.fetchall()

    items = [
        {
            "ItemId": row[0],
            "ItemName": row[1],
            "Price": row[2],
            "Availability": row[3],
            "LastUpdated": row[4],
        } for row in data
    ]

    return FileResponse(
        json.dumps(items, default=str),
        as_attachment=True,
        content_type='application/json',
        filename='nwmarketprices.json'
    )


def get_popular_items_v1(request: WSGIRequest, server_id: int) -> JsonResponse:
    return JsonResponse(get_popular_items_dict(server_id), status=status.HTTP_200_OK, safe=False)


@ratelimit(key='ip', rate='1/s', block=True)
def latest_prices_v1(request: WSGIRequest) -> JsonResponse:
    server_id = request.GET.get("server_id", "1")
    return latest_prices(request, int(server_id))

@api_view(['GET'])
@ratelimit(key='ip', rate='1/m', block=True)
def update_server_prices(request: WSGIRequest, server_id: int) -> JsonResponse:

    p = perf_counter()
    scanner_group = request.user.groups.filter(name="scanner_user")
    if not scanner_group.exists():
        return JsonResponse({"status": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    query = render_to_string("queries/get_item_data_full.sql", context={"server_id": server_id})
    with connection.cursor() as cursor:
        print(query)
        cursor.execute(query)

    return JsonResponse({"status": "ok", "calc_time": perf_counter() - p}, status=status.HTTP_201_CREATED)
