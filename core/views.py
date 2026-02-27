import csv
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DailyCheckinForm, MITSessionFormSet, SignUpForm, FocusCategoryForm
from .models import DailyCheckin, MITSession, Skill


def _is_checkin_completed(checkin):
    mits = list(checkin.mits.all())
    return len(mits) >= 1 and all(m.status == MITSession.Status.COMPLETED for m in mits)


def _current_streak(user):
    checkins = DailyCheckin.objects.filter(owner=user).prefetch_related("mits").order_by("-date")
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


def _monthly_narrative(month_sessions, completion_rate):
    completed_sessions = month_sessions.filter(status=MITSession.Status.COMPLETED)
    if not completed_sessions.exists():
        return "No Focused sessions logged this month yet. Start with one focused check-in today."

    skill_minutes = (
        completed_sessions.values("skill__name")
        .annotate(actual=Sum("actual_minutes"))
        .order_by("-actual")
    )
    top = next((s for s in skill_minutes if s["skill__name"] and (s["actual"] or 0) > 0), None)
    lead = f"Top focus so far: {top['skill__name']} ({top['actual'] or 0} min)." if top else "You have planned MITs logged, but actual minutes are still sparse."

    if completion_rate >= 80:
        tone = "Strong consistency this month. Keep the same cadence."
    elif completion_rate >= 60:
        tone = "Good momentum. Tighten follow-through on skipped Focused Sessions."
    else:
        tone = "Execution is below target. Simplify tomorrow’s first Focused session and protect the first block."

    return f"{lead} {tone}"


def landing(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "core/landing.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to Focused Time Tracker.")
            return redirect("home")
    else:
        form = SignUpForm()

    return render(request, "core/signup.html", {"form": form})


@login_required
def home(request):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_sessions = MITSession.objects.filter(
        daily_checkin__owner=request.user,
        daily_checkin__date__range=(week_start, week_end),
    )

    month_sessions = MITSession.objects.filter(
        daily_checkin__owner=request.user,
        daily_checkin__date__year=today.year,
        daily_checkin__date__month=today.month,
    )

    monthly_completion_summary = month_sessions.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
    )
    month_total = monthly_completion_summary["total"] or 0
    month_completed = monthly_completion_summary["completed"] or 0
    monthly_completion_rate = round((month_completed / month_total) * 100, 1) if month_total else 0

    summary = week_sessions.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
        actual_minutes=Sum("actual_minutes", filter=Q(status=MITSession.Status.COMPLETED)),
    )

    total = summary["total"] or 0
    completed = summary["completed"] or 0
    completion_rate = round((completed / total) * 100, 1) if total else 0
    current_streak = _current_streak(request.user)

    recent_mits = (
        MITSession.objects.select_related("daily_checkin", "skill")
        .filter(daily_checkin__owner=request.user, status=MITSession.Status.COMPLETED)
        .order_by("-daily_checkin__date", "skill__name")[:9]
    )

    daily_trend_qs = (
        week_sessions.values("daily_checkin__date")
        .annotate(actual=Sum("actual_minutes"))
        .order_by("daily_checkin__date")
    )
    daily_map = {r["daily_checkin__date"]: r["actual"] or 0 for r in daily_trend_qs}
    trend_labels, trend_actual = [], []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        trend_labels.append(day.strftime("%a %d"))
        trend_actual.append(daily_map.get(day, 0))

    monthly_trend_qs = (
        MITSession.objects.filter(daily_checkin__owner=request.user, status=MITSession.Status.COMPLETED)
        .annotate(month=TruncMonth("daily_checkin__date"))
        .values("month")
        .annotate(actual=Sum("actual_minutes"))
        .order_by("month")
    )
    month_labels = [r["month"].strftime("%b %Y") for r in monthly_trend_qs]
    month_actual = [r["actual"] or 0 for r in monthly_trend_qs]

    skill_qs = week_sessions.filter(status=MITSession.Status.COMPLETED).values("skill__name").annotate(count=Count("id")).order_by("-count")
    category_labels = [r["skill__name"] or "(No category)" for r in skill_qs]
    category_data = [r["count"] for r in skill_qs]

    goals = Skill.objects.filter(owner=request.user, is_active=True).order_by("name")
    goal_progress = []
    for g in goals:
        actual = (
            week_sessions.filter(skill=g, status=MITSession.Status.COMPLETED)
            .aggregate(v=Sum("actual_minutes"))["v"]
            or 0
        )
        target = g.weekly_goal_minutes or 0
        pct = round((actual / target) * 100, 1) if target else 0
        goal_progress.append({"name": g.name, "goal": target, "actual": actual, "pct": pct})

    incomplete_sessions = (
        week_sessions.exclude(status=MITSession.Status.COMPLETED)
        .select_related("skill", "daily_checkin")
        .order_by("-daily_checkin__date")
    )

    context = {
        "app_name": "Focused Time Tracker",
        "subtitle": "Track focused time with clarity, consistency, and momentum.",
        "summary": summary,
        "recent_mits": recent_mits,
        "completion_rate": completion_rate,
        "current_streak": current_streak,
        "trend_labels": trend_labels,
        "trend_actual": trend_actual,
        "category_labels": category_labels,
        "category_data": category_data,
        "month_labels": month_labels,
        "month_actual": month_actual,
        "monthly_narrative": _monthly_narrative(month_sessions, monthly_completion_rate),
        "goal_progress": goal_progress,
        "week_range_label": f"{week_start:%b %d} – {week_end:%b %d}",
        "incomplete_sessions": incomplete_sessions,
    }
    return render(request, "core/home.html", context)


@login_required
def checkin_create(request):
    selected_date = request.GET.get("date")
    try:
        target_date = datetime.strptime(selected_date, "%Y-%m-%d").date() if selected_date else date.today()
    except ValueError:
        target_date = date.today()

    checkin = DailyCheckin.objects.filter(owner=request.user, date=target_date).first()
    if not checkin:
        checkin = DailyCheckin(owner=request.user, date=target_date)

    if request.method == "POST":
        form = DailyCheckinForm(request.POST, instance=checkin)
        formset = MITSessionFormSet(request.POST, instance=checkin, form_kwargs={"user": request.user}, prefix="mits")

        if form.is_valid() and formset.is_valid():
            candidate = form.save(commit=False)
            existing_other = DailyCheckin.objects.filter(owner=request.user, date=candidate.date).exclude(pk=checkin.pk if checkin.pk else None).first()
            if existing_other:
                messages.info(request, f"Loaded existing daily log for {candidate.date}. Add your MITs there.")
                return redirect(f"/checkins/new/?date={candidate.date.isoformat()}")

            candidate.owner = request.user
            candidate.save()
            formset.instance = candidate
            formset.save()
            messages.success(request, "Daily log saved.")
            return redirect(f"/checkins/new/?date={candidate.date.isoformat()}")
    else:
        form = DailyCheckinForm(instance=checkin)
        formset = MITSessionFormSet(instance=checkin, form_kwargs={"user": request.user}, prefix="mits")

    logged_count = checkin.mits.count() if checkin.pk else 0
    return render(request, "core/checkin_form.html", {"form": form, "formset": formset, "logged_count": logged_count, "has_existing": bool(checkin.pk)})


@login_required
def focus_category_manage(request):
    edit_id = request.GET.get("edit")
    editing_skill = None
    if edit_id:
        editing_skill = get_object_or_404(Skill, pk=edit_id, owner=request.user)

    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "delete":
            skill_id = request.POST.get("skill_id")
            skill = get_object_or_404(Skill, pk=skill_id, owner=request.user)
            if skill.sessions.filter(daily_checkin__owner=request.user).exists():
                skill.is_active = False
                skill.save(update_fields=["is_active"])
                messages.info(request, f"{skill.name} has history, so it was deactivated instead of deleted.")
            else:
                skill.delete()
                messages.success(request, "Focus category deleted.")
            return redirect("focus_category_manage")

        if action == "update":
            skill_id = request.POST.get("skill_id")
            skill = get_object_or_404(Skill, pk=skill_id, owner=request.user)
            form = FocusCategoryForm(request.POST, instance=skill)
            if form.is_valid():
                form.save()
                messages.success(request, "Focus category updated.")
                return redirect("focus_category_manage")
            editing_skill = skill
        else:
            form = FocusCategoryForm(request.POST)
            if form.is_valid():
                skill = form.save(commit=False)
                skill.owner = request.user
                skill.save()
                messages.success(request, "Focus category saved.")
                return redirect("focus_category_manage")
    else:
        form = FocusCategoryForm(instance=editing_skill) if editing_skill else FocusCategoryForm()

    focus_categories = Skill.objects.filter(owner=request.user)
    return render(request, "core/skill_manage.html", {"form": form, "focus_categories": focus_categories, "editing_focus_category": editing_skill})


@login_required
def monthly_summary(request):
    month_str = request.GET.get("month", "")
    sessions = MITSession.objects.select_related("daily_checkin", "skill").filter(daily_checkin__owner=request.user)

    if month_str:
        try:
            selected = datetime.strptime(month_str, "%Y-%m").date()
            sessions = sessions.filter(daily_checkin__date__year=selected.year, daily_checkin__date__month=selected.month)
        except ValueError:
            month_str = ""

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="mit-summary-{month_str or "all"}.csv"'
        writer = csv.writer(response)
        writer.writerow(["Date", "Focus Category", "Task", "Planned Minutes", "Actual Minutes", "Status", "Miss Reason"])
        for s in sessions.order_by("-daily_checkin__date"):
            writer.writerow([s.daily_checkin.date, s.skill.name if s.skill else "", s.title, s.planned_minutes, s.actual_minutes or "", s.get_status_display(), s.miss_reason])
        return response

    rows = (
        sessions.annotate(month=TruncMonth("daily_checkin__date"))
        .values("month", "skill__name")
        .annotate(
            count=Count("id"),
            completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
            planned_minutes=Sum("planned_minutes"),
            actual_minutes=Sum("actual_minutes"),
        )
        .order_by("-month", "skill__name")
    )

    return render(request, "core/monthly_summary.html", {"rows": rows, "selected_month": month_str})


@login_required
def checkin_detail(request, pk):
    checkin = get_object_or_404(DailyCheckin.objects.prefetch_related("mits__skill"), pk=pk, owner=request.user)
    return render(request, "core/checkin_detail.html", {"checkin": checkin})
