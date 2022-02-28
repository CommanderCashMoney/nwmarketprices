import json
from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames, Runs, Servers, Name_cleanup
from nwmarketapp.models import Prices
from django.http import JsonResponse
import numpy as np
from django.db.models.functions import TruncDay
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
                  'server_id']

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
            add_run(serializer.data)
            un = request.user.username

            return Response({"status": True,
                             "message": "Prices Added"},
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            print(f'errors: {serializer.errors}')
            return Response({"status": False})


def add_run(data):
    sd = data[0]['timestamp']
    sid = data[0]['server_id']
    runs = Runs(start_date=sd, server_id=sid)
    runs.save()


class NameCleanupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Name_cleanup
        fields = ['bad_word', 'good_word', 'approved', 'timestamp']


class NameCleanupAPI(CreateAPIView):
    queryset = Name_cleanup.objects.all()
    serializer_class = NameCleanupSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            add_run(serializer.data)

            return Response({"status": True,
                             "message": "Name Cleanup Added"},
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            print(f'errors: {serializer.errors}')
            return Response({"status": False})


class ConfirmedNamesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Name_cleanup
        fields = ['name', 'timestamp', 'approved']


class ConfirmedNamesAPI(CreateAPIView):
    queryset = ConfirmedNames.objects.all()
    serializer_class = ConfirmedNamesSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            add_run(serializer.data)

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
    if current == previous:
        return 0
    try:
        return ((current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0
def get_price_graph_data(grouped_hist):
    price_graph_data = []
    for x in grouped_hist[-10:]:
        price_graph_data.append((x[0][0], x[0][1]))
    avg_price_graph = []

    for x in grouped_hist[-10:]:
        sum = 0
        for i in x:
            sum += i[1]
        avg_price = sum / len(x)
        avg_price = "{:.2f}".format(float(avg_price))
        avg_price_graph.append((x[0][0], avg_price))
    num_listings = []
    for x in grouped_hist[-10:]:
        unique_prices = []
        temp = set()

        for y in x:
            if y[1] not in temp:
                unique_prices.append(y[1])
                temp.add(y[1])
        num_listings.append(len(unique_prices))

    return price_graph_data, avg_price_graph, num_listings

def get_list_by_nameid(name_id, server_id):
    qs_current_price = Prices.objects.filter(name_id=name_id, server_id=server_id)
    try:
        item_name = qs_current_price.latest('name').name
    except Prices.DoesNotExist:

        return None, None, None, None, None, None, None

    hist_price = qs_current_price.values_list('timestamp', 'price').order_by('timestamp')
    last_run = Runs.objects.filter(server_id=server_id).latest('id').start_date
    #get all prices since last run
    latest_prices = list(hist_price.filter(timestamp__gte=last_run).values_list('timestamp', 'price', 'avail').order_by('price'))
    # group by days
    grouped_hist = [list(g) for _, g in itertools.groupby(hist_price, key=lambda x: x[0].date())]
    for count, val in enumerate(grouped_hist):
        grouped_hist[count].sort(key = lambda x: x[1])

    lowest_10_raw = latest_prices[:10]

    # split out dates from prices
    for idx, day_hist in enumerate(grouped_hist):
        hist_dates2, hist_price_list2 = zip(*day_hist)
        # filter outliers for each day
        filtered_prices, bad_indices = remove_outliers(np.array(hist_price_list2))
        for x in bad_indices[0][::-1]:
            zz = grouped_hist[idx][x]
            # clean otuliers group group_hist
            del grouped_hist[idx][x]


    if lowest_10_raw:
        lowest_since_last_run = lowest_10_raw
        l_dates, lprices, lavail = zip(*lowest_since_last_run)
        filtered_prices, bad_indices = remove_outliers(np.array(lprices))
        for x in bad_indices[0][::-1]:
            # clean outliers for list
            del lowest_since_last_run[x]
        recent_lowest_price = lowest_since_last_run[0][1]
        recent_price_time = lowest_since_last_run[0][0].strftime('%x %I:%M %p')
    else:
        recent_lowest = grouped_hist[-1]
        recent_lowest_price = recent_lowest[0][1]
        recent_price_time = recent_lowest[0][0].strftime('%x %I:%M %p')


    # recent_price_time = qs_current_price.values_list('timestamp').latest('timestamp')



    price_change = 0
    if len(grouped_hist) > 1:
        prev_lowest = grouped_hist[-2]
        prev_date = prev_lowest[0][0]
        prev_lowest_price = min(prev_lowest)[1]

        price_change = get_change(recent_lowest_price, prev_lowest_price)
        try:
            price_change = "{:.2f}".format(float(price_change))
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

    return grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name


@ratelimit(key='ip', rate='3/s', block=True)
# @cache_page(60 * 120)
def index(request, item_id=None, server_id=1):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
    confirmed_names = confirmed_names.values_list('name', 'id')
    all_servers = Servers.objects.all()
    all_servers = all_servers.values_list('name', 'id')


    # is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    selected_name = request.GET.get('cn_id')
    if selected_name:

        grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(selected_name, server_id)
        if not grouped_hist:
            # we didnt find any prices with that name id
            return JsonResponse({"recent_lowest_price": 'N/A', "price_change": 'Not Found', "last_checked": 'Not Found'}, status=200)

        price_graph_data, avg_price_graph, num_listings = get_price_graph_data(grouped_hist)

        return JsonResponse({"recent_lowest_price": recent_lowest_price, "last_checked": recent_price_time,
                             "price_graph_data": price_graph_data, "price_change": price_change_text, "avg_graph_data": avg_price_graph, "detail_view": lowest_10_raw, 'item_name': item_name, 'num_listings': num_listings}, status=200)


    else:

            # not an ajax post or a direct item link URL, only run this on intial page load or refresh
        popular_endgame_ids = [1223, 1496, 1421, 1626, 436, 1048, 806, 1463, 1461, 1458]
        popular_endgame_data = []
        for x in popular_endgame_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(x, server_id)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = '<span class="blue_text">&#8593;{}%</span>'.format(price_change)
            else:
                price_change = '<span class="yellow_text">&#8595;{}%</span>'.format(price_change)
            popular_endgame_data.append([item_name, recent_lowest_price, price_change, x])

        popular_base_ids = [1576,120,1566,93,1572,1166,1567,868,1571,538]
        popular_base_data = []
        for x in popular_base_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(x, server_id)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            popular_base_data.append([item_name, recent_lowest_price, price_change, x])

        mote_ids = [862,459,649,910,158,869,497]
        mote_data = []
        for x in mote_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(x, server_id)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            mote_data.append([item_name, recent_lowest_price, price_change, x])

        refining_ids = [326, 847,1033,977,1334]
        refining_data = []
        for x in refining_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(x, server_id)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            refining_data.append([item_name, recent_lowest_price, price_change, x])

        trophy_ids = [1542,1444,1529,1541,1502]
        trophy_data = []
        for x in trophy_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text, recent_price_time, lowest_10_raw, item_name = get_list_by_nameid(x, server_id)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            trophy_data.append([item_name, recent_lowest_price, price_change, x])

        # Most listed bar chart
        last_run = Runs.objects.filter(server_id=server_id).latest('id').start_date

        qs_recent_items = Prices.objects.filter(timestamp__gte=last_run, server_id=server_id).values_list('timestamp', 'price', 'name', 'name_id')
        qs_format_date = qs_recent_items.annotate(day=TruncDay('timestamp')).values_list('day', 'price', 'name')
        qs_grouped = list(qs_format_date.annotate(Count('name_id'), Count('price'), Count('day')).order_by('name'))
        d = collections.defaultdict(int)
        a = []

        for ts, price, name, c, c1, c2 in qs_grouped:
            if not name in a: a.append(name)
            d[name] += 1

        most_listed_item = sorted(d.items(), key=lambda item: item[1])
        most_listed_item_top10 = most_listed_item[-9:]


    return render(request, 'nwmarketapp/index.html', {'cn_list': confirmed_names, 'endgame': popular_endgame_data, 'base': popular_base_data, 'motes': mote_data, 'refining': refining_data, 'trophy': trophy_data, 'top10': most_listed_item_top10,
                                  "direct_link": item_id, 'servers': all_servers, 'server_id': server_id})

@ratelimit(key='ip', rate='5/s', block=True)
@cache_page(60 * 120)
def cn(request):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
    confirmed_names = list(confirmed_names.values_list('name', 'id'))
    cn = json.dumps(confirmed_names)

    return JsonResponse({'cn': cn}, status=200)

@ratelimit(key='ip', rate='5/s', block=True)
@cache_page(60 * 120)
def nc(request):
    name_cleanup = Name_cleanup.objects.all()
    name_cleanup = list(name_cleanup.values_list('bad_word', 'good_word').filter(approved=True))
    nc = json.dumps(name_cleanup)

    return JsonResponse({'nc': nc}, status=200)



