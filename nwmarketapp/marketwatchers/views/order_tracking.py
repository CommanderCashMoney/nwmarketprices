from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from nwmarketapp.models import SoldItems
from django.core.handlers.wsgi import WSGIRequest
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from ratelimit.decorators import ratelimit
from rest_framework.decorators import api_view
from django.db.models import Subquery, OuterRef
from nwmarketapp.models import Servers
from nwmarketapp.api.utils import check_scanner_status


@api_view(['GET'])
@login_required(login_url="/", redirect_field_name="")
@ratelimit(key='ip', rate='2/s', block=True)
def buy_orders(request: WSGIRequest):
    scanner_status = check_scanner_status(request)

    if not scanner_status['scanner'] or not scanner_status['recently_scanned']:
        # user hasnt done enough recent scans
        return render(request, "marketwatchers/buy_orders.html", {'error_message': "Try performing a full scan before accessing this page."})

    query = render_to_string("queries/profit_buy_orders.sql", context={"server_id": (','.join(scanner_status['server_ids']))})
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    column_names = ['Name', 'Highest Buy Order Price', 'Buy Order Qty','Lowest Sell Price', 'Sell Order Avail', 'Server Name', '% Diff']
    item_exclusion_list = ['Desert Sunrise',
                           'Pattern:'
                           ]
    for idx, item in reversed(list(enumerate(results))):
        for exclude_item in item_exclusion_list:
            if exclude_item in item[0]:
                print('removed', results[idx])
                results.pop(idx)
                break

    return render(request, "marketwatchers/buy_orders.html", {'results': results, 'column_names': column_names})


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
