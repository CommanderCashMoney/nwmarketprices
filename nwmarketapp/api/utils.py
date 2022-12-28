from collections import defaultdict
from time import perf_counter
from typing import Dict, List, Any
import cloudscraper
import concurrent
import requests
from constance import config
from nwmarketapp.models import PriceSummary


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

def get_popular_items_dict_v2(server_id) -> Any:
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
    objs = PriceSummary.objects.filter(server_id=server_id, confirmed_name_id__in=popular_items)
    return_values = defaultdict(list)
    for obj in objs:
        for k, v in popular_items_dict.items():
            if obj.confirmed_name_id in v:
                return_values[k].append(obj)
                break
    return return_values





def load_url(url, reqs=requests):
    return reqs.get(url)


def get_all_nwdb_items() -> List[Dict]:
    base_url = "https://nwdb.info/db/items/page"
    first_page = f"{base_url}/1.json"
    scraper = cloudscraper.create_scraper()
    adapter = requests.adapters.HTTPAdapter(pool_connections=500, pool_maxsize=500)
    scraper.mount("https://", adapter)
    page = scraper.get(first_page).json()
    all_nwdb_ids = []
    all_nwdb_items = []
    total_pages = page["pageCount"]
    urls = [f"{base_url}/{i+1}.json" for i in range(total_pages)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        futures = (executor.submit(load_url, url, scraper) for url in urls)
        for future in concurrent.futures.as_completed(futures):
            for res in future.result().json()["data"]:
                all_nwdb_ids.append(res["id"])

    # now the even bigger part... get all the items
    base_item_url = "https://nwdb.info/db/item"
    item_urls = [f"{base_item_url}/{item}.json" for item in all_nwdb_ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        futures = (executor.submit(load_url, url, scraper) for url in item_urls)
        for future in concurrent.futures.as_completed(futures):
            res = future.result().json()["data"]
            nwdb_id = res["id"]
            item_classes = res["itemClass"]
            not_obtainable = res.get("notObtainable") is True
            not_interested = res["typeName"] in ["Outpost Rush Resource", "Quest Item", "Event Key"]
            non_tradable_item_classes = ["OutpostRushOnly", "LootContainer", "SiegeWarOnly", "Blueprint", "Source_store"]  # noqa: E501
            for item_class in non_tradable_item_classes:
                if item_class in item_classes:
                    not_interested = True
                    break
            not_interested = not_interested or res["itemType"] in ["weapon", "armor"]
            faction_item_id_prefixes = ["faction_armaments", "faction_provisions", "faction_armorset", "workorder_"]
            for prefix in faction_item_id_prefixes:
                if prefix in nwdb_id:
                    is_faction = True
                    break
            else:
                is_faction = False
            is_bop = res.get("bindOnPickup") is True
            if not_interested or is_bop or not_obtainable or is_faction:
                continue

            all_nwdb_items.append({
                "id": nwdb_id,
                "type_name": res["typeName"],
                "name": res["name"],
                "max_stack": res["maxStack"],
                "item_class": item_classes,
                "item_type": res["itemType"]
            })
    return all_nwdb_items


