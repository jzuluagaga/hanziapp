from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    GoogleAuthView, LoginView, PasswordResetConfirmView, PasswordResetRequestView, ProfileView, RegisterView,
)

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth_register"),
    path("auth/login", LoginView.as_view(), name="auth_login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="auth_refresh"),
    path("auth/google", GoogleAuthView.as_view(), name="auth_google"),
    path("auth/password-reset", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("auth/password-reset/confirm", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("me/profile", ProfileView.as_view(), name="me_profile"),
]
