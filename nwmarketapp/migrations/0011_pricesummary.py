# Generated by Django 4.0.1 on 2022-04-23 08:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nwmarketapp', '0010_confirmednames_max_stack_confirmednames_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_id', models.IntegerField(db_index=True)),
                ('lowest_prices', models.JSONField(null=True)),
                ('graph_data', models.JSONField(null=True)),
                ('confirmed_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nwmarketapp.confirmednames')),
            ],
            options={
                'db_table': 'price_summaries',
                'unique_together': {('server_id', 'confirmed_name')},
            },
        ),
    ]
