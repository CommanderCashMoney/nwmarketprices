import json
from decimal import Decimal
from time import perf_counter
from typing import Iterable, List

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames, Runs, Servers, Name_cleanup, nwdb_lookup
from nwmarketapp.models import Prices
from django.http import JsonResponse, FileResponse
import numpy as np
from django.db.models.functions import TruncDate, TruncDay
from django.db.models import Count
import itertools
import collections
from django.views.decorators.cache import cache_page
from ratelimit.decorators import ratelimit
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from nwmarketapp.pydantic_models import ItemPriceHistory, ItemSummary
from nwmarketapp.utils import get_price_change_percent


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        # Add extra responses here
        data['username'] = self.user.username
        data['groups'] = self.user.groups.values_list('name', flat=True)

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prices
        fields = ['name',
                  'price',
                  'avail',
                  'timestamp',
                  'name_id',
                  'server_id',
                  'approved',
                  'username']

class PricesUploadAPI(CreateAPIView):
    queryset = Prices.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super(PricesUploadAPI, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            access_groups = request.user.groups.values_list('name', flat=True)
            add_run(serializer.data, access_groups)


            return Response({"status": True,
                             "message": "Prices Added"},
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            print(f'errors: {serializer.errors}')
            return Response({"status": False})


def add_run(data, access_groups):
    sd = data[0]['timestamp']
    sid = data[0]['server_id']
    un = data[0]['username']
    if 'scanner_user' in access_groups:
        approved = True
    else:
        approved = False
    runs = Runs(start_date=sd, server_id=sid, approved=approved, username=un)
    runs.save()


class NameCleanupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Name_cleanup
        fields = ['bad_word', 'good_word', 'approved', 'timestamp', 'username']


class NameCleanupAPI(CreateAPIView):
    queryset = Name_cleanup.objects.all()
    serializer_class = NameCleanupSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response({"status": True,
                             "message": "Name Cleanup Added"},
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            print(f'errors: {serializer.errors}')
            return Response({"status": False})


class ConfirmedNamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmedNames
        fields = ['name', 'timestamp', 'approved', 'username']


class ConfirmedNamesAPI(CreateAPIView):
    queryset = ConfirmedNames.objects.all()
    serializer_class = ConfirmedNamesSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            return Response({"status": True,
                             "message": "Confirmed Names Added"},
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            print(f'errors: {serializer.errors}')
            return Response({"status": False})


def check_if_outlier(price: Decimal, prices: List[Decimal], m=33) -> bool:
    median_price = np.median(prices)
    diff_arr = np.abs(prices - median_price)
    median_of_diff = np.median(diff_arr)
    price_diff_from_median = abs(price - median_price)
    diff_arr_percent = price_diff_from_median / (median_of_diff if median_of_diff else 1.)
    return diff_arr_percent > m


def remove_outliers(price_objects: Iterable[Prices], m=33) -> List[Prices]:
    data = np.array([price["price"] for price in price_objects])
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / (mdev if mdev else 1.)
    bad_indices = np.nonzero(s > m)
    return_data: List[Prices] = list(price_objects)
    for idx in bad_indices[0][::-1]:
        del return_data[idx]
    return return_data


def get_price_graph_data(grouped_hist: List[List[ItemPriceHistory]]):
    # get last 10 lowest prices
    price_graph_data = []
    for date_group in grouped_hist[-15:]:
        price_graph_data.append((date_group[0].scan_time, date_group[0].price))


    # get 15 day rolling average
    smooth = Decimal("0.3")
    i = 1
    avg = []
    avg_price_graph = []
    avg.append(price_graph_data[0][1])
    avg_price_graph.append(price_graph_data[0][1])
    while i < len(price_graph_data):
        window_average = round((smooth * price_graph_data[i][1]) + (1 - smooth) * avg[-1], 2)

        avg.append(window_average)
        avg_price_graph.append((price_graph_data[i][0], window_average))
        i += 1

    num_listings = []
    for date_group in grouped_hist[-10:]:
        unique_prices = []
        temp = set()

        for item in date_group:
            if item.price not in temp:
                if not item.quantity:
                    unique_prices.append(1)
                else:
                    unique_prices.append(item.quantity)
                temp.add(item.price)
        num_listings.append(sum(unique_prices))

    return price_graph_data[-10:], avg_price_graph[-10:], num_listings


def check_prices_arr_for_outliers(prices: Iterable[Prices]) -> List[Prices]:
    return [
        price for price in prices
        if not check_if_outlier(price.price, [price.price for price in prices])
    ]


def get_list_by_nameid(name_id, server_id) -> ItemSummary:
    last_run = Runs.objects.filter(server_id=server_id, approved=True).latest('id')
    qs_current_price = Prices.objects.filter(
        name_id=str(name_id),
        server_id=server_id,
        approved=True
    ).annotate(
        timestamp_date=TruncDate("timestamp")
    ).order_by("timestamp").values("id", "timestamp_date", "timestamp", "price", "name", "avail")
    # print(qs_current_price.explain())
    if qs_current_price.count() == 0:
        return None

    item_name = qs_current_price.latest('id')["name"]
    grouped_hist: List[List[Prices]] = [
        sorted([price for price in prices_grouped_by_date], key=lambda x: x["price"])
        for _, prices_grouped_by_date in itertools.groupby(
            qs_current_price,
            key=lambda price: price["timestamp_date"]
        )
    ]

    lowest_10_raw = qs_current_price.filter(
        username=last_run.username, timestamp__gte=last_run.start_date
    ).order_by("price")[:10]
    latest_run_has_any_of_this_item = len(lowest_10_raw) > 0

    if latest_run_has_any_of_this_item:
        recent_lowest = lowest_10_raw.first()
    else:
        recent_lowest = grouped_hist[-1][0]

    recent_lowest_price = Decimal(str(recent_lowest["price"]))
    recent_price_time = recent_lowest["timestamp"]

    summ = ItemSummary(
        grouped_hist=grouped_hist,
        recent_lowest_price=recent_lowest_price,
        recent_price_time=recent_price_time,
        lowest_10_raw=list(lowest_10_raw),
        item_name=item_name
    )
    return summ


def query_item_list(server_id: int, item_id_list: List) -> List[ItemSummary]:
    item_data = []
    for item_id in item_id_list:
        item_hist = get_list_by_nameid(item_id, server_id)
        if item_hist is None:
            continue

        if item_hist.price_change and item_hist.price_change >= 0:
            price_change = '<span class="blue_text">&#8593;{}%</span>'.format(item_hist.price_change)
        else:
            price_change = '<span class="yellow_text">&#8595;{}%</span>'.format(item_hist.price_change)
        item_data.append([item_hist.item_name, item_hist.recent_lowest_price, price_change, item_id])
    return item_data


@ratelimit(key='ip', rate='10/s', block=True)
# @cache_page(60 * 10)
def index(request, item_id=None, server_id=1):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"').filter(approved=True)
    confirmed_names = confirmed_names.values_list('name', 'id', 'nwdb_id')
    all_servers = Servers.objects.all()
    all_servers = all_servers.values_list('name', 'id')
    # is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    selected_name = request.GET.get('cn_id')
    if selected_name:
        if not selected_name.isnumeric():
            # nwdb id was passed instead. COnvert this to my ids
            selected_name = confirmed_names.get(nwdb_id=selected_name.lower())[1]

        item_history = get_list_by_nameid(selected_name, server_id)
        if not item_history.grouped_hist:
            # we didnt find any prices with that name id
            return JsonResponse({"recent_lowest_price": 'N/A', "price_change": 'Not Found', "last_checked": 'Not Found'}, status=200)

        price_graph_data, avg_price_graph, num_listings = get_price_graph_data(item_history.grouped_hist)

        try:
            nwdb_id = nwdb_lookup.objects.get(name=item_history.item_name)
            nwdb_id = nwdb_id.item_id
        except ObjectDoesNotExist:
            nwdb_id = ''

        return JsonResponse({
            "recent_lowest_price": item_history.recent_lowest_price,
            "last_checked": item_history.recent_price_time.strftime("%m/%d/%y %H:%M:%S"),
            "price_graph_data": price_graph_data,
            "price_change": item_history.price_change_text,
            "avg_graph_data": avg_price_graph,
            "detail_view": [
                item.dict() for item in
                item_history.lowest_10_raw
            ],
            'item_name': item_history.item_name,
            'num_listings': num_listings,
            'nwdb_id': nwdb_id
        }, status=200)
    else:
        popular_endgame_data = query_item_list(server_id, [1223, 1496, 1421, 1626, 436, 1048, 806, 1463, 1461, 1458])
        popular_base_data = query_item_list(server_id, [1576, 120, 1566, 93, 1572, 1166, 1567, 868, 1571, 538])
        mote_data = query_item_list(server_id, [862, 459, 649, 910, 158, 869, 497])
        refining_data = query_item_list(server_id, [326, 847, 1033, 977, 1334])
        trophy_data = query_item_list(server_id, [1542, 1444, 1529, 1541, 1502])
        # Most listed bar chart
        try:
            last_run = Runs.objects.filter(server_id=server_id).latest('id').start_date
            qs_recent_items = Prices.objects.filter(timestamp__gte=last_run, server_id=server_id).values_list(
                'timestamp', 'price', 'name', 'name_id')
            qs_format_date = qs_recent_items.annotate(day=TruncDay('timestamp')).values_list('day', 'price', 'name')
            qs_grouped = list(qs_format_date.annotate(Count('name_id'), Count('price'), Count('day')).order_by('name'))
            d = collections.defaultdict(int)
            a = []

            for ts, price, name, c, c1, c2 in qs_grouped:
                if not name in a: a.append(name)
                d[name] += 1

            most_listed_item = sorted(d.items(), key=lambda item: item[1])
            most_listed_item_top10 = most_listed_item[-9:]
        except Runs.DoesNotExist:
            most_listed_item_top10 = []

    return render(request, 'nwmarketapp/index.html', {
        'cn_list': confirmed_names,
        'endgame': popular_endgame_data,
        'base': popular_base_data,
        'motes': mote_data,
        'refining': refining_data,
        'trophy': trophy_data,
        'top10': most_listed_item_top10,
        "direct_link": item_id,
        'servers': all_servers,
        'server_id': server_id
    })

@ratelimit(key='ip', rate='10/s', block=True)
# @cache_page(60 * 120)
def cn(request):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"').filter(approved=True)
    confirmed_names = list(confirmed_names.values_list('name', 'id'))
    cn = json.dumps(confirmed_names)

    return JsonResponse({'cn': cn}, status=200)

@ratelimit(key='ip', rate='10/s', block=True)
# @cache_page(60 * 120)
def nc(request):
    name_cleanup = Name_cleanup.objects.all().filter(approved=True)
    name_cleanup = list(name_cleanup.values_list('bad_word', 'good_word').filter(approved=True))
    nc = json.dumps(name_cleanup)

    return JsonResponse({'nc': nc}, status=200)


@ratelimit(key='ip', rate='10/s', block=True)
def servers(request):
    server_list = Servers.objects.all().values_list('name', 'id'). order_by('id')
    server_list = list(server_list)
    server_list = json.dumps(server_list)

    return JsonResponse({'servers': server_list}, status=200)


@ratelimit(key='ip', rate='3/s', block=True)
def latest_prices(request: WSGIRequest) -> FileResponse:
    server_id = request.GET.get('server_id')
    if not server_id or not server_id.isnumeric():
        server_id = 1
    last_run = Runs.objects.filter(server_id=server_id, approved=True).latest('id').start_date
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






