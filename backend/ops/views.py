from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from languages.models import Language

from . import params


class HealthView(APIView):
    """Ruta de salud para el monitor externo (Q-08): consulta la base de verdad."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response({"status": "down"}, status=503)
        return Response({"status": "ok"})


class ConfigView(APIView):
    """Configuración pública que la interfaz necesita antes de acceder (Docs/10-api.md §3)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            "languages": [
                {"code": l.code, "is_study_active": l.is_study_active, "is_ui_active": l.is_ui_active}
                for l in Language.objects.all()
            ],
            "policy_version": params.value("data_policy_version"),
            "signup_mode": params.value("signup_mode"),
            "limits": {
                "new_limit_recognition": params.value("new_limit_recognition"),
                "new_limit_writing": params.value("new_limit_writing"),
            },
        })
