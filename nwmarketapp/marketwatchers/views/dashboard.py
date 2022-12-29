import time
from dateutil.parser import isoparse
from django.contrib.auth.decorators import login_required

from django.shortcuts import render

import pytz
from datetime import datetime
import json
from django.core.handlers.wsgi import WSGIRequest

from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from dateutil import parser
from ratelimit.decorators import ratelimit

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from django.db.models import Subquery, OuterRef
from nwmarketapp.views import get_serverlist
from django.contrib.postgres.fields import ArrayField

from nwmarketapp.models import PriceSummary, AuthUserTrackedItems, User
from django.views.decorators.cache import cache_page

class TrackedItemsSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = AuthUserTrackedItems
        fields = [
            'user_id',
            'item_ids',
            'server_id',

        ]

    def create(self, validated_data):

        AuthUserTrackedItems.objects.update_or_create(
            user_id=self.initial_data['user_id'],
            server_id=validated_data['server_id'],
            defaults=validated_data
        )
        return validated_data

    def update(self, instance, validated_data):

        AuthUserTrackedItems.objects.update_or_create(
            user_id=self.initial_data['user_id'],
            server_id=validated_data['server_id'],
            defaults=validated_data
        )
        return validated_data



@api_view(['POST'])
@ratelimit(key='ip', rate='1/s', block=True)
def tracked_items_save(request):
    user_id = request.user.id
    data = {
        'user_id': user_id,
        'item_ids': request.data['item_ids'],
        'server_id': request.data['server_id'],

    }
    if not data['item_ids']:
        data['item_ids'] = None
    item = TrackedItemsSerializer(data=data)

    if AuthUserTrackedItems.objects.filter(user_id=data['user_id'], server_id=data['server_id']).exists():
        # raise serializers.ValidationError('This data already exists')
        print('data already exists. doing update')

    if item.is_valid():
        item.save()
        return Response(item.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)



def dashboard(request: WSGIRequest, server_id):

    server_details = get_serverlist()

    return render(request, "marketwatchers/dashboard.html", {'servers': server_details})


# @ratelimit(key='ip', rate='1/s', block=True)
# @cache_page(60 * 10)
def price_changes(request: WSGIRequest, server_id):
    # todo confirm they are logged in and if they are a scanner
    p = time.perf_counter()
    try:
        ps = PriceSummary.objects.filter(server_id=server_id)
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
                        price_drops.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id, 'price': obj.recent_lowest_price['price'], 'price_change': obj.price_change, 'vs_avg': -abs(round(vs_avg))})

            if obj.price_change > 30:
                if obj.ordered_graph_data[-1]['rolling_average'] < obj.recent_lowest_price['price']:
                    try:
                        vs_avg = 100 - ((obj.ordered_graph_data[-1]['rolling_average'] / obj.recent_lowest_price['price']) * 100.0)
                    except ZeroDivisionError:
                        vs_avg = 0
                    if vs_avg > 20:
                        price_increases.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id, 'price': obj.recent_lowest_price['price'], 'price_change': obj.price_change, 'vs_avg': round(vs_avg)})

    price_drops = sorted(price_drops, key=lambda item: item["price_change"])[:20]
    price_increases = sorted(price_increases, key=lambda item: item["price_change"], reverse=True)[:20]


    elapsed = time.perf_counter() - p
    print('price changes process time: ', elapsed)

    return JsonResponse({'price_drops': price_drops, 'price_increases': price_increases})


def compared_to_all_servers(request: WSGIRequest, server_id):

    return None

# @ratelimit(key='ip', rate='1/s', block=True)
# @cache_page(60 * 10)
def rare_items(request: WSGIRequest, server_id):
    # todo confirm scanner status
    p = time.perf_counter()

    try:
        ps = PriceSummary.objects.filter(server_id=server_id)
    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No prices found for this item."}, status=404)

    current_time = datetime.now()
    rare_items_list = []
    for obj in ps:
        # show only items seen in the last 24 hours
        time_diff = current_time - obj.recent_price_time
        hours_since_seen = time_diff.total_seconds() / 3600
        if hours_since_seen <= 90:  # todo change back to 24
            if len(obj.ordered_graph_data) > 1:
                # prior to today, this item hasn't been seen for 7 or more days. But it was seen at least once
                previously_seen_time = parser.parse(obj.ordered_graph_data[-2]['price_date'])
                time_diff = current_time - previously_seen_time
                hours_since_previously_seen = time_diff.total_seconds() / 3600
                if hours_since_previously_seen > 168:
                    rare_items_list.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id,
                                            'price': obj.recent_lowest_price['price'],
                                            'last_seen': time_diff.days})

    rare_items_list = sorted(rare_items_list, key=lambda item: item["last_seen"])[:10]
    elapsed = time.perf_counter() - p
    print('rare item process time: ', elapsed)

    return JsonResponse({'rare_items': rare_items_list})


# @ratelimit(key='ip', rate='1/s', block=True)
# @cache_page(60 * 10)
def get_dashboard_items(request: WSGIRequest, server_id: int):
    # item_ids = [1223, 258, 1776, 166, 3943, 1627, 435, 1324, 326]
    # item_ids = []
    try:
        item_ids = AuthUserTrackedItems.objects.get(user_id=request.user.id, server_id=server_id)
    except AuthUserTrackedItems.DoesNotExist:
        return JsonResponse({"status": "No items found."}, status=404)

    item_ids = item_ids.item_ids

    try:
        ps = PriceSummary.objects.filter(server_id=server_id, confirmed_name_id__in=item_ids).select_related('confirmed_name')

    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No items found."}, status=404)

    if not ps:
        return JsonResponse({"status": "No items found."}, status=404)
    results = []
    for obj in ps:
        json_data = {
            'item_name': obj.confirmed_name.name,
            'item_id': obj.confirmed_name_id,
            'nwdb_id': obj.confirmed_name.nwdb_id,
            'lowest_price': obj.recent_lowest_price,
            'graph_data': json.dumps(obj.ordered_graph_data[-15:]),
            'price_change': obj.price_change,
            "last_checked": isoparse(obj.recent_lowest_price['datetime'])

        }
        results.append(json_data)

    response = render_to_string("marketwatchers/snippets/tracked-items.html", {'dashboard_data': results})

    return JsonResponse({'item_data': response, 'mini_graph_data': results}, safe=False)
