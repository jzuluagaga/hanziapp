from django.contrib import admin

from ops.services import audit

from .models import Grant, Plan, UsageRecord


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "version", "is_current", "created_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        audit(request.user, "plan_saved", obj, capabilities=obj.capabilities)


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    """Conceder a mano (HU-E11-03 llega en V2; mientras tanto, panel). Solo el dueño, con motivo (R-DER-12)."""

    list_display = ("account", "origin", "plan_code", "starts_at", "ends_at")
    list_filter = ("origin", "plan_code")
    search_fields = ("account__email",)
    readonly_fields = ("created_by", "created_at")

    def has_add_permission(self, request):
        return request.user.has_perm("users.owner")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("users.owner")

    def save_model(self, request, obj, form, change):
        if not obj.reason.strip():
            from django.core.exceptions import ValidationError
            raise ValidationError("Una concesión manual exige motivo.")
        obj.created_by = obj.created_by or request.user
        super().save_model(request, obj, form, change)
        audit(request.user, "grant_saved", obj, obj.reason, plan=obj.plan_code)


admin.site.register(UsageRecord)
