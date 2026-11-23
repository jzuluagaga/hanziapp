from django.contrib import admin

from .models import Deck


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("__str__", "kind", "hsk_level", "index", "retired_at")
    list_filter = ("kind", "hsk_level")
