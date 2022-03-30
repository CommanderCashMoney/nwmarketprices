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
    server_id = models.IntegerField(editable=False)
    approved = models.BooleanField(editable=False)
    username = models.CharField(max_length=100, editable=False)
    # start_date = models.DateTimeField(editable=False)
    started_at = models.DateTimeField(editable=False)
    scraper_version = models.CharField(max_length=10, editable=False)
    tz_name = models.TextField(null=True, editable=False)

    class Meta:
        db_table = 'runs'

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return f"<Run: id={self.id} server_id={self.server_id} username='{self.username}' start_date={self.started_at}>"


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
    price = models.FloatField()
    avail = models.IntegerField()
    name = models.CharField(max_length=150)
    # timestamp = models.DateTimeField()
    price_timestamp = models.DateTimeField()  # new tz aware col
    name_id = models.IntegerField(db_index=True)
    server_id = models.IntegerField()
    username = models.CharField(max_length=50)
    approved = models.BooleanField()

    class Meta:
        db_table = 'prices'

    def __str__(self):
        return f"<Price: id={self.pk} name='{self.name}' price={self.price} timestamp={self.price_timestamp}>"


class NWDBLookup(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    name = models.CharField(max_length=150, blank=True, null=True)
    item_id = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'nwdb_lookup'
