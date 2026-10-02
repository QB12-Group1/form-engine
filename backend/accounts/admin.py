from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import OTP, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "status",
        "effective_status",
        "attempts_count",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "expires_at")
    search_fields = ("email",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    exclude = ("code",)
    readonly_fields = (
        "email",
        "status",
        "effective_status",
        "attempts_count",
        "max_attempts",
        "expires_at",
        "consumed_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
