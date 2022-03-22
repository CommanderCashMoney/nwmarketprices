from django.db import connection, migrations


tz_fields = [
    ("prices", "timestamp"),
    ("confirmed_names", "timestamp"),
    ("runs", "start_date"),
    ("name_cleanup", "timestamp")
]

alter_table_template = "ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE TIMESTAMP {with_or_without} TIME ZONE;".format


def make_query(with_or_without: str) -> str:
    with connection.cursor() as cursor:
        query = "\n".join([
            alter_table_template(table_name=field[0], column_name=field[1], with_or_without=with_or_without)
            for field in tz_fields
        ])
        cursor.execute(query)


def forwards(apps, schema_editor):
    make_query("WITHOUT")


def backwards(apps, schema_editor):
    make_query("WITH")


class Migration(migrations.Migration):
    dependencies = [("nwmarketapp", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
