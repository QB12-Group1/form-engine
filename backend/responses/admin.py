from django.contrib import admin

from .models import Answer, ResponseSession


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ("question", "value", "created_at")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question")


@admin.register(ResponseSession)
class ResponseSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "survey", "is_completed", "submitted_at", "created_at")
    list_filter = ("is_completed", "created_at", "submitted_at")
    search_fields = ("=id", "survey__title", "respondent_ip")
    list_select_related = ("survey",)
    readonly_fields = (
        "survey",
        "respondent_ip",
        "user_agent",
        "is_completed",
        "submitted_at",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = (AnswerInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "session", "created_at")
    list_filter = ("created_at",)
    search_fields = ("=id", "question__title", "session__survey__title", "=session__id")
    list_select_related = ("question", "session")
    readonly_fields = ("question", "session", "value", "created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
