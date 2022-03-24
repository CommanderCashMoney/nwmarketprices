import datetime

import django
from django.db import connection, migrations, models
from django.db.migrations.state import StateApps


def update_run_ids_for_ts_range(run_id: int, obj_dict: dict) -> None:
    start_date = obj_dict["start_date"].isoformat().replace("T", " ")
    end_date = obj_dict["end_date"].isoformat().replace("T", " ")
    server_id = obj_dict["server_id"]
    approved = int(obj_dict["approved"])
    with connection.cursor() as cursor:
        cursor.execute(f"""
        UPDATE prices
        SET run_id={run_id}
        WHERE
            server_id={server_id} AND
            timestamp BETWEEN '{start_date}' AND '{end_date}' AND
            approved={approved}
        """)
    print(f"Updated run id {run_id}")


def delete_prices_before_feb():
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM prices WHERE timestamp < '2022-02-01';")


def forwards(apps: StateApps, schema_editor):
    Run = apps.get_model("nwmarketapp", "Run")  # noqa
    Prices = apps.get_model("nwmarketapp", "Price")  # noqa
    unique_server_ids = set([value[0] for value in Run.objects.all().values_list("server_id").distinct()])
    run_timestamp_ranges = {}
    for server_id in unique_server_ids:
        all_runs_for_server = Run.objects.filter(server_id=server_id).order_by("id")
        last_server_run_id: int = None
        for run in all_runs_for_server:
            if run.server_id not in run_timestamp_ranges:
                run_timestamp_ranges[run.server_id] = {}
            server_timestamp_ranges = run_timestamp_ranges[run.server_id]
            server_timestamp_ranges[run.id] = {
                "server_id": server_id,
                "start_date": run.start_date,
                "end_date": datetime.datetime.max,
                "previous_run_id": last_server_run_id,
                "approved": run.approved
            }
            if last_server_run_id is not None:
                server_timestamp_ranges[last_server_run_id]["end_date"] = run.start_date - datetime.timedelta(seconds=1)
            last_server_run_id = run.id

    for server_id, runs in run_timestamp_ranges.items():
        for run_id, run in runs.items():
            update_run_ids_for_ts_range(run_id, run)

    delete_prices_before_feb()


def backwards(apps: StateApps, schema_editor):
    pass  # no point


class Migration(migrations.Migration):
    dependencies = [
        ('nwmarketapp', '0003_rename_name_cleanup_namecleanup_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='price',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nwmarketapp.run'),
        ),
    ]
