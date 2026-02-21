from django.contrib import admin

from .models import DailyCheckin, MITSession, Skill


class MITSessionInline(admin.TabularInline):
    model = MITSession
    extra = 0


@admin.register(DailyCheckin)
class DailyCheckinAdmin(admin.ModelAdmin):
    list_display = ("owner", "date", "created_at")
    search_fields = ("date", "owner__username")
    list_filter = ("owner",)
    inlines = [MITSessionInline]


@admin.register(MITSession)
class MITSessionAdmin(admin.ModelAdmin):
    list_display = ("daily_checkin", "skill", "title", "planned_minutes", "actual_minutes", "status")
    list_filter = ("status", "skill", "daily_checkin__owner")
    search_fields = ("title", "miss_reason")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("owner", "name", "goal_minutes", "is_active", "created_at")
    list_filter = ("owner", "is_active")
    search_fields = ("name", "description", "owner__username")
