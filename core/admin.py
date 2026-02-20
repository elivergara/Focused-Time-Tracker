from django.contrib import admin

from .models import DailyCheckin, MITSession, Skill


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
    list_display = ("daily_checkin", "skill", "title", "planned_minutes", "actual_minutes", "status")
    list_filter = ("status", "skill")
    search_fields = ("title", "miss_reason")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
