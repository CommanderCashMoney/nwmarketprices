import itertools
from datetime import datetime
from typing import List

from dateutil.parser import isoparse
from django.contrib.auth.models import User
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

    class Meta:
        db_table = 'runs'

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return f"<Run: id={self.id} server_id={self.server_id} username='{self.username}' start_date={self.start_date}>"


class Servers(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)
    name = models.CharField(max_length=50, blank=True, null=True)


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
    avail = models.IntegerField()
    name = models.CharField(max_length=150)
    timestamp = models.DateTimeField()
    name_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField()
    username = models.CharField(max_length=50)
    approved = models.BooleanField()

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
            avg_qty = sum(p['single_price_avail'] for p in g) / len(g)

            for idx, item in reversed(list(enumerate(g))):
                item.update({"avg_price": avg_price})
                item.update({"avg_qty": avg_qty})
                if item['lowest_price'] <= 30:
                    if item['single_price_avail'] / avg_qty <= 0.05:
                        if item['lowest_price'] / avg_price <= 0.60:
                            # print(f'removed: {self.confirmed_name}, price of: {item["lowest_price"]}. Avg price was: {avg_price}')
                            g.pop(idx)

            lowest_price_graph.append(g[0])
        price_arr = [p['lowest_price'] for p in lowest_price_graph]
        x = 0.55  # smoothing factor for rolling average
        i = 1
        moving_averages = [price_arr[0]]
        lowest_price_graph[0].update({'rolling_average': price_arr[0]})
        while i < len(price_arr):
            window_average = round((x * price_arr[i]) +
                                   (1 - x) * moving_averages[-1], 2)
            lowest_price_graph[i].update({'rolling_average': window_average})
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

            avg_price = sum(p['price'] for p in ordered_price) / len(ordered_price)
            avg_qty = sum(p['avail'] for p in ordered_price) / len(ordered_price)

            for idx, item in reversed(list(enumerate(ordered_price))):
                if item['avail'] / avg_qty <= 0.05:
                    if item['price'] / avg_price <= 0.60:
                        # print(f'removed: {self.confirmed_name}, price of: {item["price"]}. Avg price was: {avg_price}')
                        ordered_price.pop(idx)

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

    class Meta:
        db_table = 'price_summaries'
        unique_together = (("server_id", "confirmed_name"),)


class NWDBLookup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    item_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'nwdb_lookup'
