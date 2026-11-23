from django.contrib import admin

from .models import AuditLog, Parameter
from .services import audit


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "rule", "updated_at")
    search_fields = ("key",)

    def save_model(self, request, obj, form, change):
        old = Parameter.objects.filter(pk=obj.pk).values_list("value", flat=True).first()
        super().save_model(request, obj, form, change)
        audit(request.user, "parameter_changed", obj, old=old, new=obj.value)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_id")
    list_filter = ("action", "target_type")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
