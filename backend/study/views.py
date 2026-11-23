"""
Rutas de estudio y catálogo (Docs/10-api.md §5 y §6).
"""
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services import emit
from content.models import Word
from content.services.reading import first_meanings, published_counts, published_word_ids, syllabus_totals
from decks.models import Deck
from decks.services import deck_word_ids, system_decks
from entitlements.services import allowed_levels, unlocking_plan
from hanzi_backend.exception_handlers import ApiError
from hanzi_backend.permissions import StudentAccess
from scheduling.services import is_learned, states_for
from users.services import local_day, profile_of

from . import queue, services
from .models import StudySession

SKILLS = services.SKILLS


# ───────────────────────────── Catálogo

class LevelsView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request):
        lang = profile_of(request.user).study_language_id
        totals, published, allowed = syllabus_totals(), published_counts(lang), set(allowed_levels(request.user))
        decks = {}
        for d in system_decks():
            decks[d.hsk_level] = decks.get(d.hsk_level, 0) + 1
        return Response([
            {"level": n, "total": totals[n], "published": published[n], "locked": n not in allowed,
             "unlocking_plan": None if n in allowed else unlocking_plan(n), "decks": decks.get(n, 0)}
            for n in range(1, 7)
        ])


def deck_payload(deck: Deck, account, allowed: set[int], lang: str) -> dict:
    ids = deck_word_ids(deck)
    locked = deck.hsk_level not in allowed
    counts = {s: {"due": 0, "new": 0} for s in SKILLS}
    if not locked:
        for s in SKILLS:
            c = queue.candidates(account, s, deck, apply_limit=False)
            counts[s] = {"due": len(c.due), "new": len(c.fresh)}
    return {"id": str(deck.pk), "kind": deck.kind, "level": deck.hsk_level, "index": deck.index, "size": len(ids),
            "published": len(published_word_ids(lang, ids)), "locked": locked,
            "unlocking_plan": unlocking_plan(deck.hsk_level) if locked else None, "counts": counts}


class DecksView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request):
        level = request.query_params.get("level")
        levels = [int(level)] if level and level.isdigit() else None
        lang = profile_of(request.user).study_language_id
        allowed = set(allowed_levels(request.user))
        return Response([deck_payload(d, request.user, allowed, lang) for d in system_decks(levels)])


class DeckDetailView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request, deck_id):
        deck = get_object_or_404(Deck, pk=deck_id, kind=Deck.Kind.SYSTEM, retired_at__isnull=True)
        account = request.user
        lang = profile_of(account).study_language_id
        ids = deck_word_ids(deck)
        words = {w.pk: w for w in Word.objects.filter(pk__in=ids)}
        published = published_word_ids(lang, ids)
        meanings = first_meanings(published, lang)
        states = states_for(account, "recognition", ids)
        today = local_day(account)

        def badge(pk):
            if pk not in published:
                return "in_review"
            st = states.get(str(pk))
            if st is None:
                return "new"
            if st.due_day <= today:
                return "due"
            return "learned" if is_learned(st) else "scheduled"

        emit("deck_viewed", account, deck_kind=deck.kind, hsk_level=deck.hsk_level)
        return Response({
            "deck": deck_payload(deck, account, set(allowed_levels(account)), lang),
            "words": [{"id": str(pk), "hanzi": words[pk].hanzi, "pinyin": words[pk].pinyin, "meaning": meanings.get(pk),
                       "editorial": "published" if pk in published else "in_review", "badge": badge(pk)} for pk in ids],
        })


# ───────────────────────────── Sesiones

class ScopeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["all_due", "deck"])
    deck_id = serializers.CharField(required=False)


class StartSerializer(serializers.Serializer):
    scope = ScopeSerializer()
    skill = serializers.ChoiceField(choices=SKILLS)
    chain = serializers.BooleanField(default=False)
    force = serializers.BooleanField(default=False)


def _own_session(request, session_id) -> StudySession:
    return get_object_or_404(StudySession, pk=session_id, account=request.user)


class SessionsView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request):
        qs = StudySession.objects.filter(account=request.user)
        if request.query_params.get("status") == "active":
            qs = qs.filter(status=StudySession.Status.ACTIVE)
        return Response([services.session_summary(s) for s in qs[:20]])

    def post(self, request):
        s = StartSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        deck = None
        if d["scope"]["type"] == "deck":
            deck_id = d["scope"].get("deck_id", "")
            if not deck_id.isdigit():
                raise ApiError("invalid_input", field="deck_id")
            deck = get_object_or_404(Deck, pk=int(deck_id), retired_at__isnull=True)
        r = services.start_session(request.user, skill=d["skill"], deck=deck, chain=d["chain"], force=d["force"])
        if r.kind == "conflict":
            return Response({"error": "session_exists", "detail": {}, "session": services.session_summary(r.session)},
                            status=status.HTTP_409_CONFLICT)
        if r.kind == "empty":
            return Response({"session": None, "empty_reason": r.reason})
        return Response({"session": services.session_payload(r.session)}, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request, session_id):
        return Response({"session": services.session_payload(_own_session(request, session_id))})


class SessionResumeView(APIView):
    permission_classes = [StudentAccess]

    def post(self, request, session_id):
        session = services.resume(_own_session(request, session_id), request.data.get("same_client"))
        return Response({"session": services.session_payload(session)})


class SessionDiscardView(APIView):
    permission_classes = [StudentAccess]

    def post(self, request, session_id):
        session = services.discard(_own_session(request, session_id))
        return Response({"session": services.session_summary(session)})


class WritingSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["guided", "recall"], default="recall")
    stroke_misses = serializers.IntegerField(min_value=0, max_value=200, default=0)
    hint_used = serializers.BooleanField(default=False)


class AnswerSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    position = serializers.IntegerField(min_value=0)
    unit = serializers.CharField(max_length=20)
    grade = serializers.ChoiceField(choices=["pass", "fail"], required=False, default="fail")
    choice = serializers.CharField(max_length=20, required=False, allow_blank=True)
    writing = WritingSerializer(required=False)
    answered_at = serializers.DateTimeField(required=False)
    response_ms = serializers.IntegerField(min_value=0, max_value=3_600_000, required=False)
    replays = serializers.IntegerField(min_value=0, max_value=100, required=False)
    attempts = serializers.IntegerField(min_value=1, max_value=10_000, required=False)
    first_attempt_at = serializers.DateTimeField(required=False)


class AnswersView(APIView):
    permission_classes = [StudentAccess]

    def post(self, request):
        s = AnswerSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            return Response(services.record_answer(request.user, s.validated_data))
        except services.StaleCard as e:
            e.session.refresh_from_db()
            return Response({"error": "stale_card", "detail": {}, "session": services.session_payload(e.session)},
                            status=status.HTTP_409_CONFLICT)
