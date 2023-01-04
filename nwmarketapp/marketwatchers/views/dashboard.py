import time
from dateutil.parser import isoparse
from nwmarketapp.api.utils import check_scanner_status
from django.shortcuts import render
from django.db import connection
from datetime import datetime
import json
from django.core.handlers.wsgi import WSGIRequest

from django.http import JsonResponse
from django.template.loader import render_to_string
from dateutil import parser
from ratelimit.decorators import ratelimit
from rest_framework.response import Response

from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view
from nwmarketapp.views import get_serverlist
from nwmarketapp.models import PriceSummary, AuthUserTrackedItems, ConfirmedNames
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


@ratelimit(key='ip', rate='2/s', block=True)
def dashboard(request: WSGIRequest, server_id):
    server_details = get_serverlist()

    return render(request, "marketwatchers/dashboard.html", {'servers': server_details})


@ratelimit(key='ip', rate='1/s', block=True)
@cache_page(60 * 5)
def price_changes(request: WSGIRequest, server_id):
    scanner_status = check_scanner_status(request)
    if not scanner_status['scanner'] or not scanner_status['recently_scanned']:
        if not scanner_status['discord-gold']:
            return JsonResponse({"status": "No recent scans from user"}, status=404)

    p = time.perf_counter()

    query = render_to_string("queries/largest_price_changes.sql", context={"server_id": server_id})

    try:
        ps = PriceSummary.objects.raw(query)
    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No prices found."}, status=404)


    price_drops = []
    price_increases = []

    for obj in ps:

        # if obj.recent_lowest_price['avail'] > 4:
        if obj.price_change < -40:
            if obj.ordered_graph_data[-1]['rolling_average'] > obj.recent_lowest_price['price']:
                try:
                    vs_avg = 100 - ((obj.recent_lowest_price['price'] / obj.ordered_graph_data[-1][
                        'rolling_average']) * 100.0)
                except ZeroDivisionError:
                    vs_avg = 0
                if vs_avg > 30:
                    price_drops.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id,
                                        'price': obj.recent_lowest_price['price'], 'price_change': obj.price_change,
                                        'vs_avg': -abs(round(vs_avg))})

        if obj.price_change > 800:
            if obj.ordered_graph_data[-1]['rolling_average'] < obj.recent_lowest_price['price']:
                try:
                    vs_avg = 100 - ((obj.ordered_graph_data[-1]['rolling_average'] / obj.recent_lowest_price[
                        'price']) * 100.0)
                except ZeroDivisionError:
                    vs_avg = 0
                if vs_avg > 30:
                    price_increases.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id,
                                            'price': obj.recent_lowest_price['price'],
                                            'price_change': obj.price_change, 'vs_avg': round(vs_avg)})



    price_drops = sorted(price_drops, key=lambda item: item["price_change"])[:20]
    price_increases = sorted(price_increases, key=lambda item: item["price_change"], reverse=True)[:20]

    elapsed = time.perf_counter() - p
    print('price changes process time: ', elapsed)

    return JsonResponse({'price_drops': price_drops, 'price_increases': price_increases})


@ratelimit(key='ip', rate='1/s', block=True)
@cache_page(60 * 5)
def rare_items(request: WSGIRequest, server_id):
    scanner_status = check_scanner_status(request)
    if not scanner_status['scanner'] or not scanner_status['recently_scanned']:
        if not scanner_status['discord-gold']:
            return JsonResponse({"status": "No recent scans from user"}, status=404)

    p = time.perf_counter()
    query = render_to_string("queries/rare_items.sql", context={"server_id": server_id})

    try:
        ps = PriceSummary.objects.raw(query)
    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No prices found."}, status=404)


    rare_items_list = []
    for obj in ps:

        rare_items_list.append({'item_name': obj.confirmed_name.name, 'item_id': obj.confirmed_name_id,
                                'price': obj.recent_lowest_price['price'],
                                'last_seen': obj.diff})

    rare_items_list = sorted(rare_items_list, key=lambda item: item["last_seen"], reverse=True)[:10]
    elapsed = time.perf_counter() - p
    print('rare item process time: ', elapsed)

    return JsonResponse({'rare_items': rare_items_list})


@ratelimit(key='ip', rate='1/s', block=True)
def get_dashboard_items(request: WSGIRequest, server_id: int):
    if request.user.is_anonymous:
        return JsonResponse({"status": "Not logged in"}, status=401)
    max_tracked_num = 12
    scanner_status = check_scanner_status(request)
    if not scanner_status['scanner'] or not scanner_status['recently_scanned']:
        if not scanner_status['discord-gold']:
            max_tracked_num = 6

    try:
        item_ids = AuthUserTrackedItems.objects.get(user_id=request.user.id, server_id=server_id)
    except AuthUserTrackedItems.DoesNotExist:
        return JsonResponse({"status": "No items found.", 'max_tracked_num': max_tracked_num}, status=404)

    item_ids = item_ids.item_ids
    # item_ids = item_ids[:max_tracked_num]
    try:
        ps = PriceSummary.objects.filter(server_id=server_id, confirmed_name_id__in=item_ids).select_related(
            'confirmed_name')

    except PriceSummary.DoesNotExist:
        return JsonResponse({"status": "No items found.", 'max_tracked_num': max_tracked_num}, status=404)

    if not ps:
        return JsonResponse({"status": "No items found.", 'max_tracked_num': max_tracked_num}, status=404)
    results = []
    for obj in ps:
        json_data = {
            'item_name': obj.confirmed_name.name,
            'item_id': obj.confirmed_name_id,
            'nwdb_id': obj.confirmed_name.nwdb_id,
            'lowest_price': obj.recent_lowest_price,
            'graph_data': json.dumps(obj.ordered_graph_data[-15:]),
            'price_change': obj.price_change,
            "last_checked": isoparse(obj.recent_lowest_price['datetime']),
            'server_id': server_id

        }
        results.append(json_data)
    not_found = [item for item in item_ids if not any(d['item_id'] == item for d in results)]
    for item_id in not_found:
        item_name = ConfirmedNames.objects.get(id=item_id).name
        json_data = {
            'item_name': item_name,
            'item_id': item_id,
            'nwdb_id': None,
            'lowest_price': 'N/A',
            'graph_data': None,
            'price_change': 'N/A',
            "last_checked": 'N/A',
            'server_id': server_id

        }
        results.append(json_data)


    response = render_to_string("marketwatchers/snippets/tracked-items.html", {'dashboard_data': results})

    return JsonResponse({'item_data': response, 'mini_graph_data': results, 'max_tracked_num': max_tracked_num}, safe=False)


def get_name(item):
    return item[0]

def top_sold_items(request: WSGIRequest, server_id: int):
    scanner_status = check_scanner_status(request)
    if not scanner_status['scanner'] or not scanner_status['recently_scanned']:
        if not scanner_status['discord-gold']:
            return JsonResponse({"status": "No recent scans from user"}, status=404)

    query = render_to_string("queries/most_sold_items_allservers.sql")
    with connection.cursor() as cursor:
        cursor.execute(query)
        all_servers = cursor.fetchall()

    query = render_to_string("queries/most_sold_items_server_specific.sql", context={"server_id": server_id})
    with connection.cursor() as cursor:
        cursor.execute(query)
        current_server = cursor.fetchall()

    all_servers_json = [
        {
            "ItemName": row[0],
            "ItemId": row[1],
            "AvgPrice": round(row[2], 2),
            "AvgQty": round(row[3], 2),
            "Total": row[4],

        } for row in all_servers
    ]
    current_server_json = [
        {
            "ItemName": row[0],
            "ItemId": row[1],
            "AvgPrice": round(row[2], 2),
            "AvgQty": round(row[3], 2),
            "Total": row[4],

        } for row in current_server
    ]

    return JsonResponse({'top_sold_items_allservers': all_servers_json, 'top_sold_items_currentserver': current_server_json})



