from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import gettext_lazy as _

from nwmarketapp.models import ConfirmedNames, NameCleanup, NameMap, Run


class RunAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "server_id", "username", "price_count_field", "start_date", "approved", "scraper_version", "tz_name", "price_accuracy", "name_accuracy", "resolution"]
    list_display = ["id", "server_id", "username", "price_count_field", "start_date", "price_accuracy", "name_accuracy", "resolution"]
    list_filter = ["server_id", "username", "start_date", "approved"]

    @staticmethod
    def price_count_field(obj: Run) -> int:
        return obj.price_set.count()

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


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


class NameMapAdmin(admin.ModelAdmin):
    readonly_fields = ["bad_name", "user_submitted", "user_corrected"]
    fields = ["bad_name", "correct_item", "user_submitted", "user_corrected"]
    list_display = ["bad_name", "number_times_seen", "mapped"]
    autocomplete_fields = ['correct_item']
    list_filter = [CleanupFilter]

    def mapped(self, obj: NameMap) -> bool:
        return obj.correct_item is not None

    def has_add_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj: NameMap, form, change):
        if obj.correct_item is not None:
            obj.user_corrected = request.user
        super().save_model(request, obj, form, change)

    mapped.boolean = True


class NameCleanupAdminForm(forms.ModelForm):
    def clean_good_word(self):
        good_word = self.data["good_word"]
        if not good_word or len(good_word.split(" ")) != 1:
            raise ValidationError("Good word must be a word, not multiple words.")
        count = NameCleanup.objects.filter(bad_word=good_word).exclude(id=self.instance.pk).count()
        if count > 0:
            raise ValidationError("Good word cannot be the same as a bad word.")
        return self.cleaned_data["good_word"]

    def clean_bad_word(self):
        print(self.data)
        bad_word = self.data["bad_word"]
        if not bad_word or len(bad_word.split(" ")) != 1:
            raise ValidationError("Bad word must be a word, not multiple words.")
        count = NameCleanup.objects.filter(good_word=bad_word).exclude(id=self.instance.pk).count()
        if count > 0:
            raise ValidationError("Bad word cannot be the same as a good word.")
        return self.cleaned_data["bad_word"]


class NameCleanupAdmin(admin.ModelAdmin):
    form = NameCleanupAdminForm
    readonly_fields = ["user"]
    fields = ["good_word", "bad_word", "user"]
    list_display = ["bad_word", "good_word", "user"]

    def save_model(self, request, obj: NameMap, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Run, RunAdmin)
admin.site.register(NameMap, NameMapAdmin)
admin.site.register(NameCleanup, NameCleanupAdmin)
admin.site.register(ConfirmedNames, ConfirmedNamesAdmin)
