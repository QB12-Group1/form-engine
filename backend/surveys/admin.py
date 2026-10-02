from django.contrib import admin

from .models import Question, Survey


class QuestionInline(admin.TabularInline):
    model = Question
    fields = ("title", "type", "is_required", "order")
    ordering = ("order", "pk")
    extra = 0
    show_change_link = True


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "workspace", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "workspace__name")
    autocomplete_fields = ("workspace",)
    list_select_related = ("workspace", "workspace__owner")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "survey", "type", "is_required", "order")
    list_filter = ("type", "is_required")
    search_fields = ("title", "description", "survey__title")
    autocomplete_fields = ("survey",)
    list_select_related = ("survey",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("survey", "order", "pk")
