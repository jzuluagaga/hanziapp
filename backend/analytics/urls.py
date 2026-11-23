from django.urls import path

from .views import ClientEventView

urlpatterns = [path("events", ClientEventView.as_view(), name="client_events")]
