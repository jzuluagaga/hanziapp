"""Permisos comunes a las rutas de estudiante."""
from rest_framework.permissions import IsAuthenticated

from hanzi_backend.exception_handlers import ApiError


class StudentAccess(IsAuthenticated):
    """Cuenta identificada, no suspendida y con la política vigente aceptada (R-CTA-09, R-DAT-01).
    Si hay una versión nueva sin aceptar responde 428 `policy_required` (Docs/10-api.md §1)."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.suspended_at:
            raise ApiError("account_suspended", 403)
        from privacy.services import policy_required

        if policy_required(request.user):
            raise ApiError("policy_required", 428)
        return True
