from django.shortcuts import render


def home(request):
    context = {
        "app_name": "MIT Dashboard",
        "subtitle": "Track your Most Important Tasks with clarity, consistency, and momentum.",
    }
    return render(request, "core/home.html", context)
