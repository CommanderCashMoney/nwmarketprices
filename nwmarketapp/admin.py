from django.contrib import admin

from nwmarketapp.models import Run


class RunAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "server_id", "username", "price_count_field", "started_at", "approved", "scraper_version", "tz_name"]
    list_display = ["id", "server_id", "username", "price_count_field", "started_at", "approved"]
    list_filter = ["server_id", "username", "started_at", "approved"]

    @staticmethod
    def price_count_field(obj: Run) -> int:
        return obj.price_set.count()


admin.site.register(Run, RunAdmin)
