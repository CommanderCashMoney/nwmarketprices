from django.contrib import admin

from nwmarketapp.models import Run


class RunAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "server_id", "username", "start_date", "approved"]
    list_display = ["id", "server_id", "username", "start_date", "approved"]
    list_filter = ["server_id", "username", "start_date", "approved"]


admin.site.register(Run, RunAdmin)
