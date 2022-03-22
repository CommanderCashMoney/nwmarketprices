from django.db import models


class ConfirmedNames(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='name', max_length=150, blank=True, null=True)  # Field name made lowercase.
    timestamp = models.DateTimeField(blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    nwdb_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'confirmed_names'
        ordering = ['name']

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name



class Perks(models.Model):
    id = models.IntegerField(db_column='ID', primary_key=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'perks'


class Runs(models.Model):
    start_date = models.DateTimeField(blank=True, null=True)
    id = models.AutoField(db_column='id', primary_key=True)
    server_id = models.IntegerField(blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)
    username = models.CharField(db_column='username', max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'runs'

    def __unicode__(self):
        return self.start_date

    def __str__(self):
        return self.start_date

class Servers(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'servers'

class Name_cleanup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    bad_word = models.CharField(max_length=150, blank=True, null=True)
    good_word = models.CharField(max_length=150, blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'name_cleanup'


class Prices(models.Model):
    price = models.FloatField(blank=True, null=True)
    avail = models.IntegerField(blank=True, null=True)
    gs = models.IntegerField(blank=True, null=True)
    perks = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    name_id = models.IntegerField(blank=True, null=True, db_index=True)
    server_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'prices'

    def __unicode__(self):
        return self.price
    def __str__(self):
        return self.price


class nwdb_lookup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    item_id = models.CharField(max_length=150, blank=True, null=True)
    class Meta:
        db_table = 'nwdb_lookup'


# temporarily re-adding nodes so that django_content_type migration doesn't break.
class Nodes(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)

    class Meta:
        db_table = 'nodes'
