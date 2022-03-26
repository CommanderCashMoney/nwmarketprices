import json
from time import perf_counter
from typing import Any, Dict, List, Tuple

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames, Run, Servers, NameCleanup, NWDBLookup
from nwmarketapp.models import Price
from django.http import JsonResponse, FileResponse
import numpy as np
from django.db.models.functions import TruncDate, TruncDay
from django.db.models import Count, Max, Min
import itertools
from collections import defaultdict
from django.views.decorators.cache import cache_page
from ratelimit.decorators import ratelimit
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection


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
        model = Price
        fields = [
            'name',
            'price',
            'avail',
            'timestamp',
            'name_id',
            'server_id',
            'approved',
            'username',
            'run'
        ]


class PricesUploadAPI(CreateAPIView):
    queryset = Price.objects.all()
    serializer_class = PriceSerializer
    permission_classes = (IsAuthenticated,)

    def get_request_data(self, request_data) -> Tuple[str, List[dict]]:
        bad_data = False
        if isinstance(request_data, list):
            version = "unknown"
            price_list = request_data
        elif isinstance(request_data, dict):
            version = request_data.get("version")
            price_list = request_data.get("price_data", [])
        if price_list and not isinstance(price_list[0], dict):
            raise ValidationError("Request data was malformed.")
        return version, price_list


    def create(self, request, *args, **kwargs):
        try:
            version, price_list = self.get_request_data(request.data)
        except ValidationError as e:
            return JsonResponse({
                "status": False,
                "message": e.message
            }, status=status.HTTP_400_BAD_REQUEST)
        if len(price_list) == 0:
            return JsonResponse({
                "status": False,
                "message": "No items were submitted."
            }, status=status.HTTP_200_OK)

        first_price = price_list[0]
        access_groups = request.user.groups.values_list('name', flat=True)
        username = request.user.username
        run = add_run(username, first_price, access_groups)
        run_id = getattr(run, "id", None)
        data = [
            {**price_data, **{"run": run_id, "username": username}}
            for price_data in price_list
        ]
        serializer = self.get_serializer(data=data, many=True)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(data)
            return JsonResponse({
                "status": True,
                "message": "Prices Added"
            }, status=status.HTTP_201_CREATED, headers=headers)
        else:
            if run:
                run.delete()
            return JsonResponse({
                "status": False,
                "errors": serializer.errors,
                "message": "Submitted data could not be serialized"
            }, status=status.HTTP_400_BAD_REQUEST)


def add_run(username: str, first_price: dict, access_groups) -> Run:
    if "timestamp" not in first_price or "server_id" not in first_price:
        return None
    sd = first_price['timestamp']
    sid = first_price['server_id']
    if 'scanner_user' in access_groups:
        approved = True
    else:
        approved = False
    run = Run(start_date=sd, server_id=sid, approved=approved, username=username)
    run.save()
    return run


class NameCleanupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NameCleanup
        fields = ['bad_word', 'good_word', 'approved', 'timestamp', 'username']


class NameCleanupAPI(CreateAPIView):
    queryset = NameCleanup.objects.all()
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


def remove_outliers(data, m=33):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / (mdev if mdev else 1.)
    good_list = data[s < m].tolist()
    bad_indices = np.nonzero(s > m)
    return good_list, bad_indices

def get_change(current, previous):
    current = float(current)
    previous = float(previous)
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0

def get_price_graph_data(grouped_hist):
    # get last 10 lowest prices
    price_graph_data = []
    for x in grouped_hist[-15:]:
        price_graph_data.append((x[0][0], x[0][1]))


    # get 15 day rolling average
    smooth = 0.3
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


    # for x in grouped_hist[-10:]:
    #     sum = 0
    #     for i in x:
    #         sum += i[1]
    #     avg_price = sum / len(x)
    #     avg_price = "{:.2f}".format(float(avg_price))
    #     avg_price_graph.append((x[0][0], avg_price))

    num_listings = []
    for x in grouped_hist[-10:]:
        unique_prices = []
        temp = set()

        for y in x:
            if y[1] not in temp:
                if not y[2]:
                    unique_prices.append(1)
                else:
                    unique_prices.append(y[2])
                temp.add(y[1])
        num_listings.append(sum(unique_prices))

    return price_graph_data[-10:], avg_price_graph[-10:], num_listings


def get_list_by_nameid(name_id: int, server_id: str) -> dict:
    qs_current_price = Price.objects.filter(name_id=name_id, server_id=server_id, approved=True)
    try:
        item_name = qs_current_price.latest('name').name
    except Price.DoesNotExist:

        return None, None, None, None, None, None, None

    hist_price = qs_current_price.values_list('timestamp', 'price', 'avail').order_by('timestamp')
    last_run = Run.objects.filter(server_id=server_id, approved=True).exclude(username="january").latest('id')
    #get all prices since last run
    latest_prices = list(hist_price.filter(run=last_run).values_list('timestamp', 'price', 'avail').order_by('price'))
    # group by days
    grouped_hist = [list(g) for _, g in itertools.groupby(hist_price, key=lambda x: x[0].date())]
    for count, val in enumerate(grouped_hist):
        grouped_hist[count].sort(key = lambda x: x[1])

    lowest_10_raw = latest_prices[:10]

    # split out dates from prices
    # for idx, day_hist in enumerate(grouped_hist):
    #     hist_dates2, hist_price_list2, hist_price_avail = zip(*day_hist)
    #     # filter outliers for each day
    #     filtered_prices, bad_indices = remove_outliers(np.array(hist_price_list2))
    #     for x in bad_indices[0][::-1]:
    #         zz = grouped_hist[idx][x]
    #         # clean otuliers group group_hist
    #         del grouped_hist[idx][x]


    if lowest_10_raw:
        lowest_since_last_run = lowest_10_raw
        # l_dates, lprices, lavail = zip(*lowest_since_last_run)
        # filtered_prices, bad_indices = remove_outliers(np.array(lprices))
        # for x in bad_indices[0][::-1]:
        #     # clean outliers for list
        #     del lowest_since_last_run[x]
        recent_lowest_price = lowest_since_last_run[0][1]
        recent_price_time = lowest_since_last_run[0][0].strftime('%x %I:%M %p')
    else:
        recent_lowest = grouped_hist[-1]
        recent_lowest_price = recent_lowest[0][1]
        recent_price_time = recent_lowest[0][0].strftime('%x %I:%M %p')

    price_change = 0
    if len(grouped_hist) > 1:
        prev_lowest = grouped_hist[-2]
        prev_date = prev_lowest[0][0]
        prev_lowest_price = min(prev_lowest)[1]

        price_change = get_change(recent_lowest_price, prev_lowest_price)
        try:
            price_change =round(price_change)
        except ValueError:
            price_change = 0

        if float(price_change) >= 0:
            price_change_text = '<span class="blue_text">{}% increase</span> since {}'.format(price_change,
                                                                                              prev_date.strftime("%x"))
        else:
            price_change_text = '<span class="yellow_text">{}% decrease</span> since {}'.format(price_change,
                                                                                                prev_date.strftime("%x"))
    else:
        price_change_text = 'Not enough data'

    #format numbers
    recent_lowest_price = "{:,.2f}".format(recent_lowest_price)

    return {
        "grouped_hist": grouped_hist,
        "recent_lowest_price": recent_lowest_price,
        "price_change": price_change,
        "price_change_text": price_change_text,
        "recent_price_time": recent_price_time,
        "lowest_10_raw": lowest_10_raw,
        "item_name": item_name
    }


def get_price_change_span(price_change) -> str:
    if price_change > 0:
        return '<span class="blue_text">&#8593;{}%</span>'.format(price_change)
    elif price_change < 0:
        return '<span class="yellow_text">&#8595;{}%</span>'.format(price_change)
    return ""


def get_item_data_list(server_id: int, item_id_list: List[int]) -> List[dict]:
    items_data = []
    for item_id in item_id_list:
        item_data = get_list_by_nameid(item_id, server_id)
        price_change = item_data["price_change"]
        if price_change and price_change >= 0:
            price_change = '<span class="blue_text">&#8593;{}%</span>'.format(price_change)
        else:
            price_change = '<span class="yellow_text">&#8595;{}%</span>'.format(price_change)
        items_data.append([
            item_data["item_name"],
            item_data["recent_lowest_price"],
            price_change,
            item_id
        ])
    return items_data


def get_popular_items_old(request: WSGIRequest, server_id: int) -> JsonResponse:
    p = perf_counter()
    popular_endgame_data = get_item_data_list(server_id, [1223, 1496, 1421, 1626, 436, 1048, 806, 1463, 1461, 1458])
    popular_base_data = get_item_data_list(server_id, [1576, 120, 1566, 93, 1572, 1166, 1567, 868, 1571, 538])
    mote_data = get_item_data_list(server_id, [862, 459, 649, 910, 158, 869, 497])
    refining_data = get_item_data_list(server_id, [326, 847, 1033, 977, 1334])
    trophy_data = get_item_data_list(server_id, [1542, 1444, 1529, 1541, 1502])

    response = {
        "popular_endgame_data": popular_endgame_data,
        "popular_base_data": popular_base_data,
        "mote_data": mote_data,
        "refining_data": refining_data,
        "trophy_data": trophy_data
    }
    print(perf_counter() - p)
    return JsonResponse(response)


def convert_popular_items_dict_to_old_style(popular_items_dict: dict) -> Dict[str, List]:
    p = perf_counter()
    return_value = {}
    for category, item_values in popular_items_dict.items():
        if category == "calculation_time":
            continue
        ordered_keys = sorted({
            k for k, v in item_values.items()
        }, key=lambda k: item_values[k]["order"])
        return_value[category] = []
        for key in ordered_keys:
            item = item_values[key]
            return_value[category].append([
                item["name"],
                item["min_price"] or "-",
                get_price_change_span(item["change"] or 0),
                str(item["name_id"])
            ])
    return {**return_value, **{
        "calculation_time": popular_items_dict["calculation_time"],
        "sorting_time": perf_counter() - p
    }}


def get_popular_items_dict(server_id) -> Dict[str, Dict[str, Any]]:
    popular_items_dict = {
        "popular_endgame_data": [1223, 1496, 1421, 1626, 436, 1048, 806, 1463, 1461, 1458],
        "popular_base_data": [1576, 120, 1566, 93, 1572, 1166, 1567, 868, 1571, 538],
        "mote_data": [862, 459, 649, 910, 158, 869, 497],
        "refining_data": [326, 847, 1033, 977, 1334],
        "trophy_data": [1542, 1444, 1529, 1541, 1502]
    }
    popular_items = []
    for popular_list in popular_items_dict.values():
        popular_items.extend(popular_list)
    p = perf_counter()

    # get the minimum price on each popular item for the last 2 run dates
    run_dates = Run.objects.filter(server_id=server_id, approved=True).annotate(
        start_date_date=TruncDate("start_date")
    ).values_list("start_date_date", flat=True).order_by("-start_date")
    distinct_run_dates = sorted(list(set(run_dates)), reverse=True)[:3]
    recent_runs = Run.objects.annotate(start_date_date=TruncDate("start_date")).filter(
        server_id=server_id, start_date_date__in=distinct_run_dates, approved=True
    ).order_by("-start_date_date")

    prices = Price.objects.filter(run__in=recent_runs, name_id__in=popular_items).annotate(
        price_date=TruncDate("timestamp")
    ).order_by("-price_date")
    min_prices = prices.values("price_date", "name_id", "name").annotate(min_price=Min("price"))
    max_date = prices.values("name_id", "name").annotate(max_date=Max("price_date")).order_by()
    max_date_map = {
        vals["name_id"]: vals["max_date"] for vals in max_date
    }

    return_values = defaultdict(lambda: defaultdict(dict))
    # map the category back
    for price_data in min_prices:
        name_id = price_data["name_id"]
        category = [cat for cat, ids in popular_items_dict.items() if name_id in ids][0]
        is_max_date = price_data["price_date"] == max_date_map[name_id]
        values = return_values[category][name_id]
        already_in_dict = bool(values)

        if not already_in_dict:
            values.update({
                "name_id": name_id,
                "name": price_data["name"],
                "min_price": price_data["min_price"] if is_max_date else None,
                "change": None,  # if there is only 1 day of data for this object, no change.\
                "order": popular_items.index(name_id)
            })
        elif values["change"] is None and values["min_price"] is not None:
            price_change = get_change(values["min_price"], price_data["min_price"])

            if round(price_change) != 0:
                values["change"] = round(price_change)

    return_values["calculation_time"] = perf_counter() - p
    return convert_popular_items_dict_to_old_style(return_values)


def get_popular_items(request: WSGIRequest, server_id: int) -> JsonResponse:
    return JsonResponse(get_popular_items_dict(server_id), status=status.HTTP_200_OK, safe=False)


@ratelimit(key='ip', rate='10/s', block=True)
@cache_page(60 * 10)
def index(request, item_id=None, server_id=1):
    p = perf_counter()
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"').filter(approved=True)
    confirmed_names = confirmed_names.values_list('name', 'id', 'nwdb_id')
    all_servers = Servers.objects.all()
    all_servers = all_servers.values_list('name', 'id')
    selected_name = request.GET.get('cn_id')
    if selected_name:
        if not selected_name.isnumeric():
            # nwdb id was passed instead. COnvert this to my ids
            selected_name = confirmed_names.get(nwdb_id=selected_name.lower())[1]

        item_data = get_list_by_nameid(selected_name, server_id)
        grouped_hist = item_data["grouped_hist"]
        item_name = item_data["item_name"]
        if not grouped_hist:
            # we didnt find any prices with that name id
            return JsonResponse({"recent_lowest_price": 'N/A', "price_change": 'Not Found', "last_checked": 'Not Found'}, status=200)

        price_graph_data, avg_price_graph, num_listings = get_price_graph_data(grouped_hist)

        try:
            nwdb_id = NWDBLookup.objects.get(name=item_data["item_name"])
            nwdb_id = nwdb_id.item_id
        except ObjectDoesNotExist:
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
    else:
        # not an ajax post or a direct item link URL, only run this on intial page load or refresh
        popular_items = get_popular_items_dict(server_id)
        # Most listed bar chart
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

    return render(request, 'nwmarketapp/index.html', {
        'cn_list': confirmed_names,
        'popular_items': popular_items,
        'top10': most_listed_item_top10,
        "direct_link": item_id,
        'servers': all_servers,
        'server_id': server_id,
        'render_time': perf_counter() - p
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
    name_cleanup = NameCleanup.objects.all().filter(approved=True)
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






