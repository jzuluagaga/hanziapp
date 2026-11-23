from django.contrib import admin

from .models import Deck, DeckFolder

admin.site.register(DeckFolder)
admin.site.register(Deck)
