
from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames
from nwmarketapp.models import Prices
from django.http import JsonResponse
import numpy as np
from django.db.models.functions import TruncDay
from django.db.models import Count, Max
import itertools
import collections
from django.views.decorators.cache import cache_page

def remove_outliers(data, m=9):
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
def get_list_by_nameid(name_id):
    qs_current_price = Prices.objects.filter(name_id=name_id)
    hist_price = qs_current_price.values_list('timestamp', 'price').order_by('timestamp')
    # truncate datetime to be mm/dd/yy
    trunced_days = list(hist_price.annotate(day=TruncDay('timestamp')).values_list('day', 'price'))
    # group by days
    grouped_hist = [list(g) for _, g in itertools.groupby(trunced_days, key=lambda x: x[0])]
    # split out dates from prices
    for idx, day_hist in enumerate(grouped_hist):
        hist_dates2, hist_price_list2 = zip(*day_hist)
        # filter outliers for each day
        filtered_prices, bad_indices = remove_outliers(np.array(hist_price_list2))
        for x in bad_indices[0][::-1]:
            zz = grouped_hist[idx][x]
            # clean otuliers group group_hist
            del grouped_hist[idx][x]

    recent_lowest_price = grouped_hist[-1]
    recent_lowest_price = min(recent_lowest_price)[1]
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

    return grouped_hist, recent_lowest_price, price_change, price_change_text

@cache_page(60 * 120)
def index(request):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
    confirmed_names = confirmed_names.values_list('name', 'id')

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if request.method == 'GET' and is_ajax:
        selected_name = request.GET.get('cn_id')
        if selected_name:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(selected_name)
            last_checked = grouped_hist[-1][0][0].strftime("%x")


            price_graph_data = []
            for x in grouped_hist:
                price_graph_data.append((x[0][0],min(x)[1]))

            return JsonResponse({"recent_lowest_price": recent_lowest_price, "last_checked": last_checked,
                                 "price_graph_data": price_graph_data, "price_change": price_change_text}, status=200)

        else:
            return JsonResponse({'nothing': True}, status=200)
    else:
        # not an ajax post, only run this on intial page load or refresh
        popular_endgame_ids = [1223, 1496, 1421, 1626, 436, 1048, 806]
        popular_endgame_data = []
        for x in popular_endgame_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(x)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = '<span class="blue_text">&#8593;{}%</span>'.format(price_change)
            else:
                price_change = '<span class="yellow_text">&#8595;{}%</span>'.format(price_change)
            popular_endgame_data.append([item_name, recent_lowest_price, price_change])

        popular_base_ids = [1576,120,1566,93,1572,1166,1567,868,1571,538]
        popular_base_data = []
        for x in popular_base_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(x)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            popular_base_data.append([item_name, recent_lowest_price, price_change])

        mote_ids = [862,459,649,910,158,869,497]
        mote_data = []
        for x in mote_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(x)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            mote_data.append([item_name, recent_lowest_price, price_change])

        refining_ids = [326, 847,81,203,1334]
        refining_data = []
        for x in refining_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(x)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            refining_data.append([item_name, recent_lowest_price, price_change])

        trophy_ids = [1542,1444,1529,1541,1953]
        trophy_data = []
        for x in trophy_ids:
            grouped_hist, recent_lowest_price, price_change, price_change_text = get_list_by_nameid(x)
            item_name = confirmed_names.get(id=x)[0]
            if float(price_change) >= 0:
                price_change = """<span class="blue_text">&#8593;{}%</span>""".format(price_change)
            else:
                price_change = """<span class="yellow_text">&#8595;{}%</span>""".format(price_change)
            trophy_data.append([item_name, recent_lowest_price, price_change])

        # Most listed pie chart
        qs_recent_items = list(Prices.objects.values_list('timestamp').latest('timestamp'))
        test1 = qs_recent_items[0].date()

        qs_recent_items = Prices.objects.filter(timestamp__gte=test1).values_list('timestamp', 'price', 'name', 'name_id')
        qs_format_date = qs_recent_items.annotate(day=TruncDay('timestamp')).values_list('day', 'price', 'name')
        qs_grouped = list(qs_format_date.annotate(Count('name_id'), Count('price'), Count('day')).order_by('name'))
        d = collections.defaultdict(int)
        a = []

        for ts, price, name, c, c1, c2 in qs_grouped:
            if not name in a: a.append(name)
            d[name] += 1

        most_liked_item = sorted(d.items(), key=lambda item: item[1])
        most_liked_item_top9 = most_liked_item[-9:]

    return render(request, 'nwmarketapp/index.html', {'cn_list': confirmed_names, 'endgame': popular_endgame_data, 'base': popular_base_data, 'motes': mote_data, 'refining': refining_data, 'trophy': trophy_data, 'top10': most_liked_item_top9})

