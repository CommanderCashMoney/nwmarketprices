import itertools
from datetime import datetime
from typing import List
from dateutil.parser import isoparse
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
import numpy as np



class ConfirmedNames(models.Model):
    name = models.TextField(unique=True)  # Field name made lowercase.
    nwdb_id = models.TextField(unique=True)
    item_type = models.TextField()
    item_classes = models.JSONField()
    max_stack = models.IntegerField(default=1)
    type_name = models.TextField(null=True, default=None)

    class Meta:
        db_table = 'confirmed_names'
        ordering = ['name']

    def __unicode__(self):
        return str(self.name)

    def __str__(self):
        return self.name


class Run(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    server_id = models.IntegerField(editable=False)
    approved = models.BooleanField(editable=False)
    username = models.CharField(max_length=100, editable=False)
    start_date = models.DateTimeField(editable=False)
    scraper_version = models.CharField(max_length=10, editable=False)
    tz_name = models.TextField(null=True, editable=False)
    resolution = models.CharField(max_length=50, editable=False, default="1440p")
    price_accuracy = models.DecimalField(max_length=50, max_digits=4, decimal_places=1, null=True, editable=False)
    name_accuracy = models.DecimalField(max_length=50, max_digits=4, decimal_places=1, null=True, editable=False)
    section_name = models.CharField(max_length=100, editable=False, null=True, default='Raw Resources')
    session_id = models.TextField(null=True, editable=False)

    class Meta:
        db_table = 'runs'

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return f"<Run: id={self.id} server_id={self.server_id} username='{self.username}' start_date={self.start_date}>"


class Servers(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)


    @property
    def last_updated(self) -> datetime:
        last_run = Run.objects.filter(server_id=self.id).latest('start_date')
        last_run_start_date = last_run.start_date
        return last_run_start_date


    def get_absolute_url(self):
        return "/%i/" % self.id

    class Meta:
        db_table = 'servers'


class NameCleanup(models.Model):
    bad_word = models.CharField(max_length=150, unique=True)
    good_word = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'name_cleanup'
        verbose_name = "Word Map"
        verbose_name_plural = "Word Mappings"


# non functional for now - just submit data to it until it is functional
class NameMap(models.Model):
    bad_name = models.TextField(editable=False)
    correct_item = models.ForeignKey(ConfirmedNames, null=True, on_delete=models.CASCADE)
    number_times_seen = models.IntegerField(editable=False)
    user_submitted = models.ForeignKey(User, default=3, on_delete=models.PROTECT, related_name="user_submitted")
    user_corrected = models.ForeignKey(User, null=True, on_delete=models.PROTECT, related_name="user_corrected")

    def __str__(self) -> str:
        if self.correct_item is not None:
            return f"Mapped Item: '{self.bad_name}''"
        return f"Unmapped Item: '{self.bad_name}''"

    class Meta:
        db_table = 'name_map'
        verbose_name_plural = "Name Mappings"
        verbose_name = "Name Mapping"


class Price(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    price = models.FloatField()
    avail = models.IntegerField(null=True)
    name = models.CharField(max_length=150)
    timestamp = models.DateTimeField()
    name_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField()
    username = models.CharField(max_length=50)
    approved = models.BooleanField()
    qty = models.IntegerField(null=True)


    class Meta:
        db_table = 'prices'

    def __str__(self):
        return f"<Price: id={self.pk} name='{self.name}' price={self.price} timestamp={self.timestamp}>"


class Craft(models.Model):
    item = models.ForeignKey(ConfirmedNames, on_delete=models.CASCADE, related_name="item_name")
    component = models.ForeignKey(ConfirmedNames, on_delete=models.CASCADE, related_name="component_name")
    quantity = models.IntegerField()

    class Meta:
        db_table = 'crafts'

class AuthUserTrackedItems(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    item_ids = ArrayField(models.IntegerField(null=True), null=True)
    server_id = models.IntegerField(null=True)

    class Meta:
        db_table = 'auth_user_tracked_items'

class AuthUserItemAlerts(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    server_id = models.IntegerField(null=True)
    alert_data = models.JSONField(null=True)

    class Meta:
        db_table = 'auth_user_item_alerts'


class SoldItems(models.Model):
    server_id = models.IntegerField()
    username = models.CharField(max_length=50, db_index=True)
    timestamp = models.DateTimeField()
    name = models.CharField(max_length=150)
    name_id = models.IntegerField()
    run = models.IntegerField()
    price = models.FloatField()
    qty = models.IntegerField(null=True)
    sold = models.IntegerField(null=True)
    gs = models.IntegerField(null=True)
    status = models.CharField(max_length=50, null=True)
    completion_time = models.CharField(max_length=50, null=True)
    gem = models.CharField(max_length=250, null=True)
    perk = models.CharField(max_length=250, null=True)
    approved = models.BooleanField(default=True)

    class Meta:
        db_table = 'sold_items'
        unique_together = (("server_id", "name_id", "price", "qty", "sold", "completion_time", "status", "gs", "gem", "perk", "username"),)


class PriceSummary(models.Model):
    server_id = models.IntegerField(db_index=True)
    confirmed_name = models.ForeignKey(ConfirmedNames, on_delete=models.CASCADE)
    lowest_prices = models.JSONField(null=True)
    graph_data = models.JSONField(null=True)


    @property
    def ordered_graph_data(self) -> List:

        lowest_price_graph = []
        sorted_graph = sorted(list(self.graph_data), key=lambda x: x['date_only'])
        for key, group in itertools.groupby(sorted_graph, lambda x: x['date_only']):

            g = sorted(list(group), key=lambda d: d['lowest_price'])
            avg_price = sum(p['lowest_price'] for p in g) / len(g)
            avg_avail = sum(p['single_price_avail'] for p in g) / len(g)
            max_price = max(p['lowest_price'] for p in g)
            buy_orders = []

            for idx, item in reversed(list(enumerate(g))):
                buy_orders.append(item.get('highest_buy_order', None))
                item.update({"avg_price": avg_price})
                item.update({"avg_avail": avg_avail})
                if item['lowest_price'] <= 30:
                    try:
                        avail_diff = item['single_price_avail'] / avg_avail
                    except ZeroDivisionError:
                        avail_diff = 1/avg_avail
                    if avail_diff <= 0.22:
                        if item['lowest_price'] / avg_price <= 0.55:
                            g.pop(idx)
                            continue
                    elif item['lowest_price'] / avg_price <= 0.05 and max_price < 50 and avail_diff <= 0.8 and avg_avail > 5 and len(g) > 8:
                        g.pop(idx)
                        print(f'removed: {self.confirmed_name.name} with price of {item["lowest_price"]} on {self.server_id} with date: {item["date_only"]}')
                        continue


            highest_bo = max([i for i in buy_orders if i is not None], default=0)
            if highest_bo == 0:
                highest_bo = None
            g[0]['highest_buy_order'] = highest_bo  # set the highest buy order price before we might have had to pop one for an outlier
            lowest_price_graph.append(g[0])

        lowest_price_graph = lowest_price_graph[-15:]
        price_arr = [p['lowest_price'] for p in lowest_price_graph]

        i = 1
        moving_averages = []
        cum_sum = np.cumsum(price_arr)
        while i <= len(price_arr):
            window_average = round(cum_sum[i - 1] / i, 2)
            moving_averages.append(window_average)
            lowest_price_graph[i-1].update({'rolling_average': window_average})
            i += 1

        return lowest_price_graph

    @property
    def ordered_price_data(self) -> List:
        return sorted(self.lowest_prices, key=lambda obj: obj["price"])

    @property
    def recent_price_time(self) -> datetime:
        return isoparse(self.ordered_graph_data[-1]["price_date"])

    @property
    def recent_lowest_price(self) -> float:
        if not self.lowest_prices:
            return None
        ordered_price = self.ordered_price_data
        if ordered_price[0]["price"] < 30:
            ordered_price = self.filter_price_ouliers(ordered_price)

            return ordered_price[0]
        else:
            return self.ordered_price_data[0]

    @property
    def price_change_dict(self) -> dict:
        from nwmarketapp.api.utils import get_change
        graph_data = self.ordered_graph_data
        graph_data.reverse()
        initial_price = self.recent_lowest_price['price']

        if len(graph_data) > 1:
            change = get_change(initial_price, graph_data[1]["lowest_price"])
            return {
                "price_change_date": isoparse(graph_data[1]["price_date"]),
                "price_change": round(change)
            }
        return {
            "price_change_date": isoparse(graph_data[0]["price_date"]),
            "price_change": 0
        }

    @property
    def price_change(self) -> float:
        return self.price_change_dict["price_change"]

    @property
    def price_change_date(self) -> datetime:
        return self.price_change_dict["price_change_date"]

    @staticmethod
    def filter_price_ouliers(price_list: list) -> List:
        buy_orders = []
        avg_price = sum(p['price'] for p in price_list) / len(price_list)
        avg_qty = sum(p['avail'] for p in price_list) / len(price_list)
        if avg_qty == 0 or avg_qty is None:
            avg_qty = 1
        max_price = max(p['price'] for p in price_list)
        for idx, item_price in reversed(list(enumerate(price_list))):
            buy_orders.append((item_price.get('buy_order_price', None), item_price.get('qty', None)))

            try:
                avail_diff = item_price['avail'] / avg_qty
            except ZeroDivisionError:
                avail_diff = 1 / avg_qty


            try:
                price_diff = item_price['price'] / avg_price
            except ZeroDivisionError:
                price_diff = 1 / avg_price

            if avail_diff <= 0.22:
                price_diff = item_price['price'] / avg_price
                if price_diff <= 0.55:
                    price_list.pop(idx)
                    continue
            elif price_diff <= 0.05 and max_price < 50 and avail_diff <= 0.8 and avg_qty > 5 and len(price_list) >= 9:
                price_list.pop(idx)

                continue

        highest_buy_order = max(buy_orders, key=lambda tup: (tup[0]) if (tup[0]) else 0)
        price_list[0]['buy_order_price'] = highest_buy_order[
            0]  # set the highest buy order price before we might have popped it in the code above when remove lowest price outliers
        price_list[0]['qty'] = highest_buy_order[1]

        return price_list

    class Meta:
        db_table = 'price_summaries'
        unique_together = (("server_id", "confirmed_name"),)


class NWDBLookup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    item_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'nwdb_lookup'
