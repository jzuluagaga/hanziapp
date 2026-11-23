from django.contrib import admin, messages

from . import services
from .models import CustomUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(CustomUser)
class AccountAdmin(admin.ModelAdmin):
    """Suspender y reactivar solo lo hace el dueño, con motivo y auditoría (R-CTA-09, R-DAT-10)."""

    list_display = ("email", "cohort", "date_joined", "last_login", "suspended_at", "is_staff")
    list_filter = ("cohort", "is_staff")
    search_fields = ("email",)
    readonly_fields = ("last_login", "date_joined", "suspended_at", "password")
    exclude = ("user_permissions",)
    inlines = [ProfileInline]
    actions = ["suspend_accounts", "reactivate_accounts"]

    def _owner(self, request):
        if not request.user.has_perm("users.owner"):
            self.message_user(request, "Solo el dueño suspende o reactiva cuentas.", messages.ERROR)
            return False
        return True

    @admin.action(description="Suspender (motivo: acción manual desde el panel)")
    def suspend_accounts(self, request, queryset):
        if self._owner(request):
            for account in queryset:
                services.suspend(account, request.user, "Suspensión manual desde el panel")

    @admin.action(description="Reactivar")
    def reactivate_accounts(self, request, queryset):
        if self._owner(request):
            for account in queryset:
                services.reactivate(account, request.user, "Reactivación manual desde el panel")
