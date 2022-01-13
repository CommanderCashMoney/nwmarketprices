from django.db import models


class ConfirmedNames(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='name', max_length=50, blank=True, null=True)  # Field name made lowercase.
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'confirmed_names'
        ordering = ['name']
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.name



class Nodes(models.Model):
    loc = models.FloatField(db_column='LOC', blank=True, null=True)  # Field name made lowercase.
    type = models.CharField(db_column='TYPE', max_length=50, blank=True, null=True)  # Field name made lowercase.
    id = models.IntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    dir = models.IntegerField(db_column='DIR', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'nodes'

class Perks(models.Model):
    id = models.IntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'perks'


class Prices(models.Model):
    price = models.FloatField(blank=True, null=True)
    avail = models.IntegerField(blank=True, null=True)
    gs = models.IntegerField(blank=True, null=True)
    perks = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prices'

