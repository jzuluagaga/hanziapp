from django.urls import path

from .views import (
    AnswersView, DeckDetailView, DecksView, LevelsView, SessionDetailView, SessionDiscardView, SessionResumeView,
    SessionsView,
)

urlpatterns = [
    path("levels", LevelsView.as_view(), name="levels"),
    path("decks", DecksView.as_view(), name="decks"),
    path("decks/<int:deck_id>", DeckDetailView.as_view(), name="deck_detail"),
    path("sessions", SessionsView.as_view(), name="sessions"),
    path("sessions/<uuid:session_id>", SessionDetailView.as_view(), name="session_detail"),
    path("sessions/<uuid:session_id>/resume", SessionResumeView.as_view(), name="session_resume"),
    path("sessions/<uuid:session_id>/discard", SessionDiscardView.as_view(), name="session_discard"),
    path("answers", AnswersView.as_view(), name="answers"),
]
