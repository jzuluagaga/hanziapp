from django.urls import path

from .views import ReportView, SearchView, WordDetailView, WordListView

urlpatterns = [
    path("words", WordListView.as_view(), name="word_list"),
    path("words/search", SearchView.as_view(), name="word_search"),
    path("words/<int:word_id>", WordDetailView.as_view(), name="word_detail"),
    path("words/<int:word_id>/reports", ReportView.as_view(), name="word_report"),
]
