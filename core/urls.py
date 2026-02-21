from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("app/", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("checkins/new/", views.checkin_create, name="checkin_create"),
    path("checkins/<int:pk>/", views.checkin_detail, name="checkin_detail"),
    path("skills/", views.skill_manage, name="skill_manage"),
    path("summary/monthly/", views.monthly_summary, name="monthly_summary"),
]
