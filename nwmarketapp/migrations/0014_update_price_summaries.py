from django.conf import settings
from django.db import migrations, connection
from django.template.loader import render_to_string

from nwmarketapp.api.views.prices import update_server_prices


def update_price_summaries(apps, schema_editor):
    Servers = apps.get_model("nwmarketapp", "Servers")
    all_servers = Servers.objects.all().values("name", "id")
    for obj in all_servers:
        query = render_to_string("queries/get_item_data_full.sql", context={"server_id": obj["id"]})
        with connection.cursor() as cursor:
            cursor.execute(query)

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nwmarketapp', '0013_auto_20220909_0949'),
    ]

    operations = [

        migrations.RunPython(update_price_summaries, backwards),

    ]
