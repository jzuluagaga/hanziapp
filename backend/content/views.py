"""Diccionario para estudiantes (HU-E07-01, HU-E07-02, HU-E07-04). Gratuito en todos los niveles (R-CON-09)."""
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services import emit
from hanzi_backend.exception_handlers import ApiError
from hanzi_backend.permissions import StudentAccess
from users.services import profile_of

from .models import ContentReport, Word
from .services.reading import first_meanings, published_word_ids, search, word_payloads


class SearchView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request):
        q = (request.query_params.get("q") or "")[:60]
        lang = profile_of(request.user).study_language_id
        kind, ids = search(q, lang)
        if q.strip():
            emit("search_performed", request.user, query_kind=kind, result_count=len(ids))
        words = {w.pk: w for w in Word.objects.filter(pk__in=ids)}
        published = published_word_ids(lang, ids)
        meanings = first_meanings(published, lang)
        return Response([
            {"id": str(pk), "hanzi": words[pk].hanzi, "pinyin": words[pk].pinyin, "level": words[pk].hsk_level,
             "meaning": meanings.get(pk), "editorial": "published" if pk in published else "in_review"}
            for pk in ids
        ])


class WordListView(APIView):
    """Palabras de un nivel para el diccionario (HU-E07-02). Gratuito en todos los niveles."""

    permission_classes = [StudentAccess]

    def get(self, request):
        level = request.query_params.get("level", "")
        if not level.isdigit() or not 1 <= int(level) <= 6:
            raise ApiError("invalid_input", field="level")
        lang = profile_of(request.user).study_language_id
        words = list(Word.objects.filter(hsk_level=int(level), retired_at__isnull=True).order_by("syllabus_order"))
        published = published_word_ids(lang, [w.pk for w in words])
        meanings = first_meanings(published, lang)
        return Response([
            {"id": str(w.pk), "hanzi": w.hanzi, "pinyin": w.pinyin, "level": w.hsk_level, "meaning": meanings.get(w.pk),
             "editorial": "published" if w.pk in published else "in_review"}
            for w in words
        ])


class WordDetailView(APIView):
    permission_classes = [StudentAccess]

    def get(self, request, word_id):
        word = get_object_or_404(Word, pk=word_id)
        lang = profile_of(request.user).study_language_id
        payload = word_payloads([word.pk], lang)[word.pk]
        origin = request.query_params.get("from")
        emit("word_viewed", request.user, hsk_level=word.hsk_level, editorial=payload["editorial"],
             **({"from": origin} if origin in ("search", "deck", "card") else {}))
        return Response(payload)


class ReportSerializer(serializers.Serializer):
    element = serializers.CharField()
    comment = serializers.CharField(allow_blank=True, max_length=1000, required=False, default="")


class ReportView(APIView):
    permission_classes = [StudentAccess]

    def post(self, request, word_id):
        word = get_object_or_404(Word, pk=word_id)
        s = ReportSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        element = s.validated_data["element"]
        if element not in ContentReport.Element.values:
            raise ApiError("invalid_input", field="element")
        report = ContentReport.objects.create(word=word, account=request.user, element=element,
                                              comment=s.validated_data["comment"].strip())
        emit("content_report_submitted", request.user, element=element, hsk_level=word.hsk_level)
        return Response({"id": str(report.pk), "status": report.status}, status=201)
