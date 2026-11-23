from django.contrib import admin

from .models import Consent, PolicyAcceptance


@admin.register(PolicyAcceptance)
class PolicyAcceptanceAdmin(admin.ModelAdmin):
    list_display = ("account", "version", "accepted_at")
    readonly_fields = ("account", "version", "accepted_at")


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("account", "purpose", "granted", "policy_version", "created_at")
    list_filter = ("purpose", "granted")
    readonly_fields = ("account", "purpose", "granted", "policy_version", "created_at")
