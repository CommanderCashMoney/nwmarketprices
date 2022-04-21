import logging

import django
from django.core.management.base import BaseCommand

from nwmarketapp.api.utils import get_all_nwdb_items
from nwmarketapp.models import ConfirmedNames


class Command(BaseCommand):
    help = 'Update ConfirmedNames from NWDB'

    def handle(self, *args, **kwargs):
        print("Fetching items from NWDB... this takes a while and can possibly crash")
        all_nwdb_items = get_all_nwdb_items()
        print("Updating ConfirmedNames with new data from NWDB")
        for item in all_nwdb_items:
            try:
                cn = ConfirmedNames.objects.get(nwdb_id=item["id"])
            except ConfirmedNames.DoesNotExist:
                cn = ConfirmedNames(nwdb_id=item["id"])

            cn.name = item["name"]
            cn.item_type = item["item_type"]
            cn.item_classes = item["item_class"]
            cn.max_stack = item["max_stack"]
            cn.type_name = item["type_name"]
            duplicated = []
            try:
                cn.save()
            except django.db.utils.IntegrityError:
                print(f"Failed duplication constraint on {cn.name}")
                duplicated.append(cn.name)
            print(json.dumps({"status": "completed", "duplicated_items": duplicated}, indent=2))
