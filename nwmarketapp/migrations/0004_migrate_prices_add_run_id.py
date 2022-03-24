import datetime

import django
from django.db import connection, migrations, models
from django.db.migrations.state import StateApps

FAKE_RUN_USER = "january"


def update_run_ids_for_ts_range(run_id: int, obj_dict: dict) -> None:
    start_date = obj_dict["start_date"].isoformat().replace("T", " ")
    end_date = obj_dict["end_date"].isoformat().replace("T", " ")
    server_id = obj_dict["server_id"]
    approved = obj_dict["approved"]
    query = f"""
    UPDATE prices
    SET run_id={run_id}
    WHERE
        server_id={server_id} AND
        timestamp BETWEEN '{start_date}' AND '{end_date}' AND
        approved={approved}
    """
    print(f"Updating run id {run_id}")
    print(query)
    with connection.cursor() as cursor:
        cursor.execute(query)
    print(f"Done\n===================================")


def forwards(apps: StateApps, schema_editor):
    Run = apps.get_model("nwmarketapp", "Run")  # noqa
    Prices = apps.get_model("nwmarketapp", "Price")  # noqa

    uther_run_mismatched_approve = Run.objects.get(id=199)
    uther_run_mismatched_approve.approved = False
    uther_run_mismatched_approve.save()

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
                one_second_before_this_run = run.start_date - datetime.timedelta(seconds=1)
                server_timestamp_ranges[last_server_run_id]["end_date"] = one_second_before_this_run
                id_from_2_runs_ago = server_timestamp_ranges[last_server_run_id]["previous_run_id"]
                # super hack to handle cases where there were overlapping runs
                unapproved_overlapping_runs = [117, 133, 129]
                if last_server_run_id in unapproved_overlapping_runs:
                    server_timestamp_ranges[id_from_2_runs_ago]["end_date"] = one_second_before_this_run

            last_server_run_id = run.id

    fake_run = Run(server_id=1, approved=False, username=FAKE_RUN_USER, start_date=datetime.datetime.utcnow())
    fake_run.save()

    with connection.cursor() as cursor:
        cursor.execute(f"""
            UPDATE prices
            SET run_id={fake_run.id}
            WHERE timestamp < '2022-02-01'
        """)

    for server_id, runs in run_timestamp_ranges.items():
        for run_id, run in runs.items():
            update_run_ids_for_ts_range(run_id, run)

    # if we reach the end of the script with no errors, all price:run data has integrity!


def backwards(apps: StateApps, schema_editor):
    Run = apps.get_model("nwmarketapp", "Run")  # noqa
    Run.objects.filter(username=FAKE_RUN_USER).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('nwmarketapp', '0003_rename_name_cleanup_namecleanup_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='price',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nwmarketapp.run', null=True),
        ),
    ]
