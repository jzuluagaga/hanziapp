"""`answer_recorded(account, counted, local_day, skill)`: `progress` escucha (09-arquitectura.md §2)."""
from django.dispatch import Signal

answer_recorded = Signal()
