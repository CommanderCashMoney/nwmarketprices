from django.contrib import admin

from nwmarketapp.models import Run


class RunAdmin(admin.ModelAdmin):
    list_display = ["id", "server_id", "username", "start_date"]
    list_filter = ["server_id", "username", "start_date"]


admin.site.register(Run, RunAdmin)
