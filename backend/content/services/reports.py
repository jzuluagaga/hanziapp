"""Atender reportes de error (HU-E13-05, R-CON-14, R-DAT-10)."""
from django.db import transaction
from django.utils import timezone

from analytics.services import emit
from ops.services import audit

from ..models import ContentReport
from .editorial import require_editor


@transaction.atomic
def close_report(report: ContentReport, user, outcome: str, reason: str) -> ContentReport:
    """`outcome` es `fixed` (resuelto) o `dismissed` (descartado). Si la resolución cambia el
    contenido, la corrección va por una versión nueva (R-CON-05), no por aquí."""
    require_editor(user)
    if outcome not in ("fixed", "dismissed"):
        raise ValueError(outcome)
    if not reason.strip():
        raise ValueError("Cerrar un reporte exige motivo.")
    report.status = ContentReport.Status.RESOLVED if outcome == "fixed" else ContentReport.Status.DISMISSED
    report.resolution = reason
    report.resolved_at = timezone.now()
    report.save(update_fields=["status", "resolution", "resolved_at"])
    audit(user, "content_report_closed", report, reason, outcome=outcome)
    emit("content_report_resolved", outcome=outcome, days_open=(report.resolved_at - report.created_at).days)
    return report
