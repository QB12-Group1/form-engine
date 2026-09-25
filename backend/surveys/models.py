from django.db import models
from django.utils.translation import gettext_lazy as _


class Survey(models.Model):
    class SurveyStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        CLOSED = "closed", _("Closed")

    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="surveys"
    )
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=50, choices=SurveyStatus.choices, default=SurveyStatus.DRAFT
    )
    settings = models.JSONField(default=dict)
    logic_rules = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    class QuestionType(models.TextChoices):
        TEXT = "text", _("Text")
        SINGLE_CHOICE = "singleChoice", _("SingleChoice")
        MULTIPLE_CHOICE = "multipleChoice", _("MultipleChoice")
        DROPDOWN = "dropdown", _("Dropdown")
        RATING = "rating", _("Rating")

    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="questions"
    )
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=50, choices=QuestionType.choices, default=QuestionType.TEXT
    )
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    properties = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
