from django.contrib import admin

from .models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "created_at", "updated_at")
    search_fields = ("name", "owner__username", "owner__email")
    list_filter = ("created_at",)
    autocomplete_fields = ("owner", "members")
    list_select_related = ("owner",)
    readonly_fields = ("invite_token", "created_at", "updated_at")
    exclude = ("password",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
