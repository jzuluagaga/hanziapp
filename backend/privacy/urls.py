from django.urls import path

from .views import ConsentView, MeView, PolicyAcceptView

urlpatterns = [
    path("me", MeView.as_view(), name="me"),
    path("me/policy/accept", PolicyAcceptView.as_view(), name="me_policy_accept"),
    path("me/consents/<str:purpose>", ConsentView.as_view(), name="me_consent"),
]
