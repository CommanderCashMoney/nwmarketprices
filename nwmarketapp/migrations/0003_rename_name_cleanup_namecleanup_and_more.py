from django.db import connection, migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('nwmarketapp', '0002_remove_tz_support'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Name_cleanup',
            new_name='NameCleanup',
        ),
        migrations.RenameModel(
            old_name='nwdb_lookup',
            new_name='NWDBLookup',
        ),
        migrations.DeleteModel(
            name='nodes',
        ),
        migrations.DeleteModel(
            name='Perks',
        ),
        migrations.AlterModelOptions(
            name='runs',
            options={'verbose_name_plural': 'Runs'},
        ),
        migrations.AddField(
            model_name='prices',
            name='run',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='nwmarketapp.runs'),
        ),
        migrations.RenameModel(
            old_name='Prices',
            new_name='Price',
        ),
        migrations.RenameModel(
            old_name='Runs',
            new_name='Run',
        ),
    ]
