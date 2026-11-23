from django.urls import path

from .views import ProgressView, TodayView

urlpatterns = [
    path("today", TodayView.as_view(), name="today"),
    path("progress", ProgressView.as_view(), name="progress"),
]
