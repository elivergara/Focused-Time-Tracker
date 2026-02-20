from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("checkins/new/", views.checkin_create, name="checkin_create"),
    path("checkins/<int:pk>/", views.checkin_detail, name="checkin_detail"),
    path("checkins/<int:pk>/edit/", views.checkin_edit, name="checkin_edit"),
    path("summary/monthly/", views.monthly_summary, name="monthly_summary"),
]
