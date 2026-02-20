from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DailyCheckin(models.Model):
    date = models.DateField(unique=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Daily Check-in {self.date}"


class MITSession(models.Model):
    class Category(models.TextChoices):
        BIBLE = "bible", "Bible"
        GUITAR = "guitar", "Guitar"
        WORK_SKILL = "work_skill", "Work/Skill"
        CUSTOM_SKILL = "custom_skill", "Custom Skill"

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    daily_checkin = models.ForeignKey(DailyCheckin, on_delete=models.CASCADE, related_name="mits")
    category = models.CharField(max_length=24, choices=Category.choices)
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
        ordering = ["daily_checkin__date", "category"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.title} ({self.planned_minutes}m)"
