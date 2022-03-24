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
        return str(self.name)

    def __str__(self):
        return self.name


class Run(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    server_id = models.IntegerField(blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)
    username = models.CharField(blank=True, max_length=100, null=True)
    start_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'runs'

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return f"<Run: id={self.id} server_id={self.server_id} username='{self.username}'>"


class Servers(models.Model):
    id = models.IntegerField(db_column='id', primary_key=True)
    name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'servers'


class NameCleanup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    bad_word = models.CharField(max_length=150, blank=True, null=True)
    good_word = models.CharField(max_length=150, blank=True, null=True)
    approved = models.BooleanField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'name_cleanup'


class Price(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"<Price: id={self.pk} name='{self.name}' price={self.price} timestamp={self.timestamp}>"


class NWDBLookup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    item_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'nwdb_lookup'
