import time
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from nwmarketapp.models import SoldItems, Servers, Run
import pytz
from datetime import datetime


from django.core.handlers.wsgi import WSGIRequest
from django.db import connection

from django.http import FileResponse, JsonResponse, HttpResponse
from django.template.loader import render_to_string

from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view
from django.db.models import Subquery, OuterRef
from nwmarketapp.api.views.prices import get_item_data
from nwmarketapp.api.utils import get_dashboard_items
from nwmarketapp.models import Craft, PriceSummary, Run, ConfirmedNames, Price, Servers


@login_required(login_url="/", redirect_field_name="")
def marketwatchers(request):
    scanner_group = request.user.groups.filter(name="scanner_user")
    if not scanner_group.exists():
        return HttpResponse("This feature is restricted to MarketWatchers only. Sign up to be a scanner on the <a href='https://discord.gg/k8AyA5Je2F'>Discord site.</a> ")

    server_name = Servers.objects.filter(id=OuterRef('server_id')).order_by('-id')
    sold_items = SoldItems.objects.filter(username=request.user.username).distinct('name', 'price', 'gs', 'qty', 'sold', 'status')
    column_names = ['Name', 'Price', 'Gear Score', 'Qty', 'Sold', 'Status', 'Completion Time', 'Scanned', 'Server']
    sold_items = list(sold_items.values_list('name', 'price', 'gs', 'qty', 'sold', 'status', 'completion_time', 'timestamp').annotate(rundate=Subquery(server_name.values('name')[:1])))

    return render(request, "marketwatchers/index.html", {'sold_items': sold_items, 'sold_item_columns': column_names})


def dashboard(request: WSGIRequest):
    # todo get user saved items from cookie
    server_id = 2
    tracked_items = [1223, 258, 1776, 166, 3943, 1627, 435, 1324, 326]
    results = get_dashboard_items(server_id, tracked_items)
    test1 = price_changes(request, 2)

    return render(request, "marketwatchers/dashboard.html", {'dashboard_data': results})

def price_changes(request: WSGIRequest, server_id):
    # todo confirm they are logged in and if they are a scanner
    p = time.perf_counter()
    try:
        ps = PriceSummary.objects.filter(server_id=2)
    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No prices found for this item."}, status=404)

    price_drops = []
    price_increases = []
    for obj in ps:
        if obj.recent_lowest_price['avail'] > 4:
            if obj.price_change < -30:
                if obj.ordered_graph_data[-1]['rolling_average'] > obj.recent_lowest_price['price']:
                    try:
                        vs_avg = 100 - ((obj.recent_lowest_price['price'] / obj.ordered_graph_data[-1]['rolling_average']) * 100.0)
                    except ZeroDivisionError:
                        vs_avg = 0
                    if vs_avg > 20:
                        price_drops.append({'item_name': obj.confirmed_name.name, 'change': obj.price_change, 'vs_avg': round(vs_avg)})

            if obj.price_change > 30:
                if obj.ordered_graph_data[-1]['rolling_average'] < obj.recent_lowest_price['price']:
                    try:
                        vs_avg = 100 - ((obj.ordered_graph_data[-1]['rolling_average'] / obj.recent_lowest_price['price']) * 100.0)
                    except ZeroDivisionError:
                        vs_avg = 0
                    if vs_avg > 20:
                        price_increases.append({'item_name': obj.confirmed_name.name, 'change': obj.price_change, 'vs_avg': round(vs_avg)})

    price_drops = sorted(price_drops, key=lambda item: item["change"])[:20]
    price_increases = sorted(price_increases, key=lambda item: item["change"], reverse=True)[:20]


    elapsed = time.perf_counter() - p
    print('process time: ', elapsed)

    return None

def compared_to_all_servers(request: WSGIRequest, server_id):

    return None


@api_view(['GET'])
@login_required(login_url="/", redirect_field_name="")
@ratelimit(key='ip', rate='2/s', block=True)
def buy_orders(request: WSGIRequest):

    scanner_groups = []
    for g in request.user.groups.all():
        scanner_groups.append(g.name)
    if 'scanner_user' not in scanner_groups:
        return HttpResponse("This feature is restricted to MarketWatchers only. Sign up to be a scanner on the <a href='https://discord.gg/k8AyA5Je2F'>Discord site.</a> ")
    server_ids = []
    for group in scanner_groups:
        if 'server-' in group:
            server_ids.append(group[group.index("-")+1:])
    # Get users last scan date. If it's more than 24 hours old show no data.
    # if they have less than 10 scans they have never run a full scan, show no data
    all_runs = Run.objects.filter(username=request.user.username)
    num_runs = all_runs.count()
    last_run = all_runs.latest('start_date')
    last_run_timestamp = last_run.start_date
    tz = pytz.timezone(last_run.tz_name)
    last_scan_utc = tz.normalize(tz.localize(last_run_timestamp)).astimezone(pytz.utc)
    last_scan_utc = last_scan_utc.replace(tzinfo=None)
    current_utc_time = datetime.utcnow()
    time_diff = current_utc_time - last_scan_utc
    hours_since_last_scan = time_diff.total_seconds()/3600
    if hours_since_last_scan > 24 or num_runs < 10:
        # user hasnt done enough recent scans
        return render(request, "marketwatchers/buy_orders.html", {'error_message': "Try performing a full scan before accessing this page."})

    query = render_to_string("queries/profit_buy_orders.sql", context={"server_id": (','.join(server_ids))})
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    column_names = ['Name', 'Highest Buy Order Price', 'Buy Order Qty','Lowest Sell Price', 'Sell Order Avail', 'Server Name', '% Diff']
    item_exclusion_list = ['Desert Sunrise',
                           'Pattern: Floral Regent Trousers',
                           'Pattern: Floral Regent Tunic',
                           'Pattern: Floral Regent Gloves',
                           'Pattern: Floral Regent Loafers',
                           'Pattern: Floral Regent Crown',
                           'Pattern: Frostbarrel',
                           'Pattern: Frozen Shard',
                           'Pattern: Holly Regent Mitts',
                           'Pattern: Tip of the Iceberg',
                           "Pattern: Winter's Warhammer",
                           'Pattern: Holly Regent Footwear',
                           "Pattern: Blizzard's Fury",
                           'Pattern: Festive Sled',
                           'Pattern: Oak Regent Chestguard',
                           'Pattern: Iceburst'
                           ]
    for idx, item in reversed(list(enumerate(results))):
        if item[0] in item_exclusion_list:
            results.pop(idx)


    # p = time.perf_counter()
    # try:
    #     ps = PriceSummary.objects.filter(server_id=2)
    # except (PriceSummary.DoesNotExist):
    #     return JsonResponse({"status": "No prices found for this item."}, status=404)
    #
    # all_item_ids = ps.values_list('confirmed_name_id')
    # all_price_changes = []
    # for item_id in all_item_ids:
    #     item_data_json = get_item_data(request, server_id=2, item_id=str(item_id[0]))
    #     all_price_changes.append(item_data_json)
    # #     try:
    # #         ps = PriceSummary.objects.get(server_id=7, confirmed_name_id=item_id)
    # #         all_price_changes.append({'item_name': ps.confirmed_name.name, 'change': ps.price_change})
    # #     except (PriceSummary.DoesNotExist):
    # #         continue
    # #
    # # all_price_changes = sorted(all_price_changes, key=lambda obj: obj["change"])
    # elapsed = time.perf_counter() - p
    # print('process time: ', elapsed)


    return render(request, "marketwatchers/buy_orders.html", {'results': results, 'column_names': column_names})
