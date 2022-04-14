import itertools
from collections import defaultdict
from time import perf_counter
from typing import Dict, List, Any

import cloudscraper
import concurrent
import numpy as np
import requests
from constance import config
from django.db.models import Min, Max
from django.db.models.functions import TruncDate

from nwmarketapp.models import Run, Price


def check_version_compatibility(version: str) -> bool:
    try:
        major, minor, patch = [int(vn) for vn in version.split(".")]
    except ValueError:
        return False

    block_on_diff = config.BLOCK_LOGIN_ON_SCANNER_DIFF
    server_major, server_minor, server_patch = [int(vn) for vn in config.LATEST_SCANNER_VERSION.split(".")]
    major_diff = server_major - major != 0
    minor_diff = server_minor - minor != 0
    patch_diff = server_patch - patch != 0
    if block_on_diff == 3 and major_diff:  # major
        return False
    elif block_on_diff == 2 and (major_diff or minor_diff):
        return False
    elif block_on_diff == 1 and (major_diff or minor_diff or patch_diff):
        return False

    return True


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
        return None

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


def get_price_change_span(price_change) -> str:
    if price_change > 0:
        return '<span class="blue_text">&#8593;{}%</span>'.format(price_change)
    elif price_change < 0:
        return '<span class="yellow_text">&#8595;{}%</span>'.format(price_change)

    return '<span class="grey_text">0%</span>'


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


def load_url(url, reqs=requests):
    return reqs.get(url)


def get_all_nwdb_items() -> List[Dict]:
    base_url = "https://nwdb.info/db/items/page"
    first_page = f"{base_url}/1.json"
    scraper = cloudscraper.create_scraper()
    page = scraper.get(first_page).json()
    all_nwdb_ids = []
    all_nwdb_items = []
    total_pages = page["pageCount"]
    urls = [f"{base_url}/{i+1}.json" for i in range(total_pages)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=total_pages) as executor:
        futures = (executor.submit(load_url, url, scraper) for url in urls)
        for future in concurrent.futures.as_completed(futures):
            for res in future.result().json()["data"]:
                all_nwdb_ids.append(res["id"])

    # now the even bigger part... get all the items
    base_item_url = "https://nwdb.info/db/item"
    item_urls = [f"{base_item_url}/{item}.json" for item in all_nwdb_ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=250) as executor:
        futures = (executor.submit(load_url, url, scraper) for url in item_urls)
        for future in concurrent.futures.as_completed(futures):
            res = future.result().json()["data"]
            is_boe = res.get("bindOnEquip") is True
            is_bop = res.get("bindOnPickup", False) is not True
            all_nwdb_items.append({
                "id": res["id"],
                "type_name": res["typeName"],
                "name": res["name"],
                "max_stack": res["maxStack"],
                "can_trade": is_boe or not is_bop,
                "item_class": res["itemClass"]
            })
    return all_nwdb_items
