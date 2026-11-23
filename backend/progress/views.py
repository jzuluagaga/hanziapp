from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services import emit
from hanzi_backend.permissions import StudentAccess
from study import queue
from study.services import SKILLS, active_sessions, recent_decks, session_summary, total_counted
from users.services import local_day

from .models import DayRecord
from .services import close_days, progress_summary, streak


class TodayView(APIView):
    """«Hoy» (HU-E03-01, HU-E06-02, HU-E09-02)."""

    permission_classes = [StudentAccess]

    def get(self, request):
        account = request.user
        close_days(account)
        counts = {s: queue.counts(account, s) for s in SKILLS}
        emit("home_viewed", account, due_recognition=counts["recognition"]["due"],
             due_listening=counts["listening"]["due"], due_writing=counts["writing"]["due"],
             new_available=sum(c["new"] for c in counts.values()))
        return Response({
            "today": local_day(account), "counts": counts,
            "active_sessions": [session_summary(s) for s in active_sessions(account)],
            "streak": streak(account), "recent_decks": recent_decks(account),
            "days": list(DayRecord.objects.filter(account=account).order_by("-day").values("day", "status")[:14]),
        })


class ProgressView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request):
        close_days(request.user)
        emit("progress_viewed", request.user)
        return Response({**progress_summary(request.user), "total_answers": total_counted(request.user)})
