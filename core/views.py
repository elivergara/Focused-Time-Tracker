from datetime import date

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DailyCheckinForm, MITSessionFormSet
from .models import DailyCheckin, MITSession


def home(request):
    today = date.today()
    month_sessions = MITSession.objects.filter(daily_checkin__date__year=today.year, daily_checkin__date__month=today.month)

    summary = month_sessions.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=MITSession.Status.COMPLETED)),
        planned_minutes=Sum("planned_minutes"),
        actual_minutes=Sum("actual_minutes"),
    )

    recent_mits = MITSession.objects.select_related("daily_checkin").order_by("-daily_checkin__date", "category")[:9]

    context = {
        "app_name": "MIT Dashboard",
        "subtitle": "Track your Most Important Tasks with clarity, consistency, and momentum.",
        "summary": summary,
        "recent_mits": recent_mits,
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

    return render(request, "core/checkin_form.html", {"form": form, "formset": formset})


def monthly_summary(request):
    monthly = (
        MITSession.objects.annotate(month=TruncMonth("daily_checkin__date"))
        .values("month", "category")
        .annotate(
            count=Count("id"),
            completed=Count("id"),
            planned_minutes=Sum("planned_minutes"),
            actual_minutes=Sum("actual_minutes"),
        )
        .order_by("-month", "category")
    )

    # Correct completed counts with explicit filter (kept simple for template use)
    rows = []
    for row in monthly:
        month = row["month"]
        category = row["category"]
        completed = MITSession.objects.filter(
            daily_checkin__date__year=month.year,
            daily_checkin__date__month=month.month,
            category=category,
            status=MITSession.Status.COMPLETED,
        ).count()
        row["completed"] = completed
        rows.append(row)

    return render(request, "core/monthly_summary.html", {"rows": rows})


def checkin_detail(request, pk):
    checkin = get_object_or_404(DailyCheckin.objects.prefetch_related("mits"), pk=pk)
    return render(request, "core/checkin_detail.html", {"checkin": checkin})
