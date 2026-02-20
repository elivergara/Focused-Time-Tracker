from collections import defaultdict
from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DailyCheckinForm, MITSessionFormSet
from .models import DailyCheckin, MITSession


def _is_checkin_completed(checkin):
    mits = list(checkin.mits.all())
    return len(mits) == 3 and all(m.status == MITSession.Status.COMPLETED for m in mits)


def _current_streak():
    checkins = DailyCheckin.objects.prefetch_related("mits").order_by("-date")
    if not checkins.exists():
        return 0

    streak = 0
    expected_date = date.today()
    checkin_map = {c.date: c for c in checkins}

    while True:
        checkin = checkin_map.get(expected_date)
        if not checkin or not _is_checkin_completed(checkin):
            break
        streak += 1
        expected_date = expected_date - timedelta(days=1)

    return streak


def home(request):
    today = date.today()
    month_sessions = MITSession.objects.filter(daily_checkin__date__year=today.year, daily_checkin__date__month=today.month)

    summary = month_sessions.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
        planned_minutes=Sum("planned_minutes"),
        actual_minutes=Sum("actual_minutes"),
    )

    total = summary["total"] or 0
    completed = summary["completed"] or 0
    completion_rate = round((completed / total) * 100, 1) if total else 0
    current_streak = _current_streak()

    recent_mits = MITSession.objects.select_related("daily_checkin").order_by("-daily_checkin__date", "category")[:9]

    # Last 6 months trend
    trend_qs = (
        MITSession.objects.annotate(month=TruncMonth("daily_checkin__date"))
        .values("month")
        .annotate(
            planned=Sum("planned_minutes"),
            actual=Sum("actual_minutes"),
            completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
            total=Count("id"),
        )
        .order_by("month")
    )

    trend_labels = []
    trend_planned = []
    trend_actual = []
    trend_completion_rate = []
    for row in trend_qs:
        trend_labels.append(row["month"].strftime("%b %Y"))
        trend_planned.append(row["planned"] or 0)
        trend_actual.append(row["actual"] or 0)
        total_row = row["total"] or 0
        comp_row = row["completed"] or 0
        trend_completion_rate.append(round((comp_row / total_row) * 100, 1) if total_row else 0)

    # Category breakdown for current month
    category_qs = (
        month_sessions.values("category")
        .annotate(count=Count("id"), completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)))
        .order_by("category")
    )
    category_counts = defaultdict(int)
    for row in category_qs:
        category_counts[row["category"]] = row["count"]

    context = {
        "app_name": "MIT Dashboard",
        "subtitle": "Track your Most Important Tasks with clarity, consistency, and momentum.",
        "summary": summary,
        "recent_mits": recent_mits,
        "completion_rate": completion_rate,
        "current_streak": current_streak,
        "trend_labels": trend_labels,
        "trend_planned": trend_planned,
        "trend_actual": trend_actual,
        "trend_completion_rate": trend_completion_rate,
        "category_labels": ["Bible", "Guitar", "Work/Skill"],
        "category_data": [
            category_counts[MITSession.Category.BIBLE],
            category_counts[MITSession.Category.GUITAR],
            category_counts[MITSession.Category.WORK_SKILL],
        ],
    }
    return render(request, "core/home.html", context)


def checkin_create(request):
    checkin = DailyCheckin()

    if request.method == "POST":
        form = DailyCheckinForm(request.POST, instance=checkin)
        formset = MITSessionFormSet(request.POST, instance=checkin)
        if form.is_valid() and formset.is_valid():
            checkin = form.save()
            formset.instance = checkin
            formset.save()
            messages.success(request, "Daily MIT check-in saved.")
            return redirect("home")
    else:
        form = DailyCheckinForm(instance=checkin, initial={"date": date.today()})
        formset = MITSessionFormSet(
            instance=checkin,
            initial=[
                {"category": MITSession.Category.BIBLE, "status": MITSession.Status.PLANNED},
                {"category": MITSession.Category.GUITAR, "status": MITSession.Status.PLANNED},
                {"category": MITSession.Category.WORK_SKILL, "status": MITSession.Status.PLANNED},
            ],
        )

    return render(request, "core/checkin_form.html", {"form": form, "formset": formset, "mode": "create"})


def checkin_edit(request, pk):
    checkin = get_object_or_404(DailyCheckin, pk=pk)

    if request.method == "POST":
        form = DailyCheckinForm(request.POST, instance=checkin)
        formset = MITSessionFormSet(request.POST, instance=checkin)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Check-in updated.")
            return redirect("checkin_detail", pk=checkin.pk)
    else:
        form = DailyCheckinForm(instance=checkin)
        formset = MITSessionFormSet(instance=checkin)

    return render(request, "core/checkin_form.html", {"form": form, "formset": formset, "mode": "edit", "checkin": checkin})


def monthly_summary(request):
    rows = (
        MITSession.objects.annotate(month=TruncMonth("daily_checkin__date"))
        .values("month", "category")
        .annotate(
            count=Count("id"),
            completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
            planned_minutes=Sum("planned_minutes"),
            actual_minutes=Sum("actual_minutes"),
        )
        .order_by("-month", "category")
    )

    return render(request, "core/monthly_summary.html", {"rows": rows})


def checkin_detail(request, pk):
    checkin = get_object_or_404(DailyCheckin.objects.prefetch_related("mits"), pk=pk)
    return render(request, "core/checkin_detail.html", {"checkin": checkin})
