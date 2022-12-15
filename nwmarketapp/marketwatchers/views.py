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
                           'Pattern: Holly Regent Footwear'
                           ]
    for idx, item in reversed(list(enumerate(results))):
        if item[0] in item_exclusion_list:
            results.pop(idx)


    return render(request, "marketwatchers/buy_orders.html", {'results': results, 'column_names': column_names})
