from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from nwmarketapp.models import SoldItems, Servers
from django.db.models import Subquery, OuterRef


@login_required(login_url="/", redirect_field_name="")
def marketwatchers(request):
    server_name = Servers.objects.filter(id=OuterRef('server_id')).order_by('-id')
    sold_items = SoldItems.objects.filter(username=request.user.username).distinct('name', 'price', 'gs', 'qty', 'sold', 'status')
    column_names = ['Name', 'Price', 'Gear Score', 'Qty', 'Sold', 'Status', 'Completion Time', 'Scanned', 'Server']
    sold_items = list(sold_items.values_list('name', 'price', 'gs', 'qty', 'sold', 'status', 'completion_time', 'timestamp').annotate(rundate=Subquery(server_name.values('name')[:1])))

    return render(request, "marketwatchers/index.html", {'sold_items': sold_items, 'sold_item_columns': column_names})
