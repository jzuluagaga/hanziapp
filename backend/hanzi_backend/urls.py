"""
Rutas del proyecto. La API vive bajo /api/v1/ (Docs/10-api.md); cada módulo
expone las suyas. Las rutas heredadas (/api/words, /api/decks, /api/token)
quedan retiradas.
"""
from django.contrib import admin
from django.urls import include, path

from analytics.views import dashboard

v1 = [
    path("", include("ops.urls")),
    path("", include("users.urls")),
    path("", include("privacy.urls")),
    path("", include("content.urls")),
    path("", include("study.urls")),
    path("", include("progress.urls")),
    path("", include("analytics.urls")),
]

urlpatterns = [
    path("admin/analytics/", dashboard, name="analytics_dashboard"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(v1)),
]
