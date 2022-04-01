from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

from nwmarketapp.models import ConfirmedNames, NameCleanupV2, Run


class RunAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "server_id", "username", "price_count_field", "start_date", "approved", "scraper_version", "tz_name"]
    list_display = ["id", "server_id", "username", "price_count_field", "start_date", "approved"]
    list_filter = ["server_id", "username", "start_date", "approved"]

    @staticmethod
    def price_count_field(obj: Run) -> int:
        return obj.price_set.count()


class ConfirmedNamesAdmin(admin.ModelAdmin):
    search_fields = ("name", )

    def get_model_perms(self, request):
        return {}  # don't display this in the list of available admins


class CleanupFilter(SimpleListFilter):
    title = _('Unmapped Items')

    parameter_name = 'correct_item'

    def lookups(self, request, model_admin):
        return (
            (None, _('Unmapped')),
            ('confirmed', _('Mapped')),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset.filter(correct_item=None)
        return queryset.exclude(correct_item=None)


class NameCleanupAdmin(admin.ModelAdmin):
    readonly_fields = ["bad_name", "user_submitted", "user_corrected"]
    fields = ["bad_name", "correct_item", "user_submitted", "user_corrected"]
    list_display = ["bad_name", "number_times_seen", "mapped"]
    autocomplete_fields = ['correct_item']
    list_filter = [CleanupFilter]

    def mapped(self, obj: NameCleanupV2) -> bool:
        return obj.correct_item is not None

    def has_add_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj: NameCleanupV2, form, change):
        if obj.correct_item is not None:
            obj.user_corrected = request.user
        super().save_model(request, obj, form, change)

    mapped.boolean = True


admin.site.register(Run, RunAdmin)
admin.site.register(NameCleanupV2, NameCleanupAdmin)
admin.site.register(ConfirmedNames, ConfirmedNamesAdmin)
