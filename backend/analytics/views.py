from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from hanzi_backend.exception_handlers import ApiError

from . import metrics
from .schemas import CLIENT_EVENTS, SCHEMAS
from .services import EventSchemaError, emit


class ClientEventSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60)
    props = serializers.DictField(required=False, default=dict)


class ClientEventView(APIView):
    """Eventos que nacen en el navegador (HU-E00-02, criterio 5)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ClientEventSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        name, props = s.validated_data["name"], s.validated_data["props"]
        if name not in CLIENT_EVENTS:
            raise ApiError("event_not_allowed")
        for k, v in props.items():
            if k not in SCHEMAS[name] or not isinstance(v, (str, int, float, bool)) or (isinstance(v, str) and len(v) > 40):
                raise ApiError("invalid_input", field=k)
        try:
            emit(name, request.user, **props)
        except EventSchemaError:
            raise ApiError("invalid_input")
        return Response(status=202)


@staff_member_required
def dashboard(request):
    """Tablero del dueño (HU-E14-01): solo agregados por cohorte."""
    if not request.user.has_perm("analytics.view_dashboard"):
        raise PermissionDenied
    return render(request, "analytics/dashboard.html", {"m": metrics.summary(), "title": "Retención y aprendizaje"})
