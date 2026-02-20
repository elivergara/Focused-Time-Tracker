from django.contrib import admin

from .models import DailyCheckin, MITSession


class MITSessionInline(admin.TabularInline):
    model = MITSession
    extra = 0


@admin.register(DailyCheckin)
class DailyCheckinAdmin(admin.ModelAdmin):
    list_display = ("date", "created_at")
    search_fields = ("date",)
    inlines = [MITSessionInline]


@admin.register(MITSession)
class MITSessionAdmin(admin.ModelAdmin):
    list_display = ("daily_checkin", "category", "title", "planned_minutes", "actual_minutes", "status")
    list_filter = ("category", "status")
    search_fields = ("title",)
