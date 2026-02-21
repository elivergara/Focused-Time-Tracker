from django.conf import settings
from django.db import models


class Skill(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills", null=True, blank=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    goal_minutes = models.PositiveIntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_skill_per_owner"),
        ]

    def __str__(self):
        return self.name


class DailyCheckin(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_checkins", null=True, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "date"], name="unique_checkin_date_per_owner"),
        ]

    def __str__(self):
        return f"Daily Check-in {self.date}"


class MITSession(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    daily_checkin = models.ForeignKey(DailyCheckin, on_delete=models.CASCADE, related_name="mits")
    category = models.CharField(max_length=24, blank=True, default="")  # legacy field
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name="sessions")
    title = models.CharField(max_length=200)
    planned_minutes = models.PositiveIntegerField()
    actual_minutes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PLANNED)
    miss_reason = models.CharField(max_length=255, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["daily_checkin__date", "skill__name", "title"]

    def __str__(self):
        skill_name = self.skill.name if self.skill else "Unassigned"
        return f"{skill_name}: {self.title} ({self.planned_minutes}m)"
