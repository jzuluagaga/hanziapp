"""
Rutas de cuenta y acceso (Docs/10-api.md §4). Errores como claves (R-IDI-03).
"""
import logging

import resend
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from analytics.services import emit
from hanzi_backend.exception_handlers import ApiError
from languages.models import Language
from ops import params

from . import services
from .emails import build_password_reset_email
from .models import CustomUser

password_reset_token_generator = PasswordResetTokenGenerator()
logger = logging.getLogger(__name__)


def tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class AuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    policy_version = serializers.CharField(allow_blank=True, default="")
    is_adult = serializers.BooleanField(default=False)
    reminder_consent = serializers.BooleanField(default=False)
    cohort = serializers.CharField(max_length=60, allow_blank=True, required=False, default="")
    timezone = serializers.CharField(max_length=64, allow_blank=True, required=False, default="")


class RegisterView(AuthView):
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = services.register(
            name=d["name"], email=d["email"], password=d["password"], policy_version=d["policy_version"],
            is_adult=d["is_adult"], reminder_consent=d["reminder_consent"], cohort=d["cohort"], tz=d["timezone"],
        )
        return Response(tokens_for_user(user), status=status.HTTP_201_CREATED)


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()


class LoginView(AuthView):
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = services.login(s.validated_data["email"], s.validated_data["password"])
        return Response(tokens_for_user(user))


class GoogleAuthView(AuthView):
    """Acceso con Google (HU-E02-03, V2). Sin aceptación de política: se pedirá al entrar (R-DAT-01)."""

    def post(self, request):
        token = request.data.get("id_token")
        if not token or not settings.GOOGLE_CLIENT_ID:
            raise ApiError("not_authenticated", 401)
        try:
            idinfo = google_id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
        except ValueError:
            raise ApiError("not_authenticated", 401)
        email = (idinfo.get("email") or "").lower()
        if not email or not idinfo.get("email_verified"):  # R-CTA-07
            raise ApiError("not_authenticated", 401)
        user = CustomUser.objects.filter(email__iexact=email).first()
        if user is None:
            raise ApiError("google_signup_not_available", 403)  # el registro con Google llega en V2
        if user.suspended_at:
            raise ApiError("account_suspended", 403)
        emit("login_succeeded", user, method="google")
        return Response(tokens_for_user(user))


class PasswordResetRequestView(AuthView):
    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        generic = Response({"ok": True}, status=status.HTTP_200_OK)
        user = CustomUser.objects.filter(email__iexact=email).first() if email else None
        if user is None:
            return generic
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/recover-access?uid={uid}&token={token}"
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY vacío: no se envía el correo de recuperación")
            return generic
        resend.api_key = settings.RESEND_API_KEY
        html, attachments = build_password_reset_email(user, reset_link)
        try:
            resend.Emails.send({
                "from": "HanziApp <noreply@hanziapp.co>", "to": [user.email],
                "subject": "Restablece tu contraseña de HanziApp", "html": html, "attachments": attachments,
            })
        except Exception:
            logger.exception("Fallo al enviar el correo de recuperación")
        return generic


class PasswordResetConfirmView(AuthView):
    def post(self, request):
        uid, token, new_password = (request.data.get(k) or "" for k in ("uid", "token", "new_password"))
        try:
            user = CustomUser.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            raise ApiError("reset_link_invalid")
        if not password_reset_token_generator.check_token(user, token):
            raise ApiError("reset_link_invalid")
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            raise ApiError("weak_password", codes=[err.code for err in e.error_list])
        user.set_password(new_password)
        user.save()  # cambia el hash: el mismo enlace deja de ser válido
        emit("password_reset_completed", user)
        return Response({"ok": True})


# ───────────────────────────── Perfil (HU-E10-01)

class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, required=False, allow_blank=False)
    ui_language = serializers.CharField(required=False)
    study_language = serializers.CharField(required=False)
    timezone = serializers.CharField(required=False)
    new_limit_recognition = serializers.IntegerField(required=False)
    new_limit_writing = serializers.IntegerField(required=False)
    theme = serializers.ChoiceField(choices=["system", "light", "dark"], required=False)


def profile_payload(profile) -> dict:
    return {
        "name": profile.name, "ui_language": profile.ui_language_id, "study_language": profile.study_language_id,
        "timezone": profile.timezone, "new_limit_recognition": profile.new_limit_recognition,
        "new_limit_writing": profile.new_limit_writing, "theme": profile.theme,
    }


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        s = ProfileSerializer(data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        profile = services.profile_of(request.user)
        changed = []
        for field, flag in (("ui_language", "is_ui_active"), ("study_language", "is_study_active")):
            if field in d and d[field] != getattr(profile, f"{field}_id"):
                if not Language.objects.filter(code=d[field], **{flag: True}).exists():
                    raise ApiError("language_inactive", field=field)
                setattr(profile, f"{field}_id", d[field])
                changed.append(field)
        for field in ("new_limit_recognition", "new_limit_writing"):
            if field in d and d[field] != getattr(profile, field):
                rng = params.value(field)
                if not rng["min"] <= d[field] <= rng["max"]:
                    raise ApiError("limit_out_of_range", field=field, min=rng["min"], max=rng["max"])
                setattr(profile, field, d[field])
                changed.append(field)
        if "timezone" in d and d["timezone"] != profile.timezone:
            if not services.valid_timezone(d["timezone"]):
                raise ApiError("timezone_invalid")
            services.change_timezone(profile, d["timezone"])
            changed.append("timezone")
        for field in ("name", "theme"):
            if field in d and d[field] != getattr(profile, field):
                setattr(profile, field, d[field].strip() if field == "name" else d[field])
                changed.append(field)
        if changed:
            profile.save()
            emit("profile_updated", request.user, fields=changed)
        return Response(profile_payload(profile))
