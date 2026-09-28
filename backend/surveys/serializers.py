from typing import Any

from rest_framework import serializers

from workspaces.models import Workspace

from .models import Question, Survey

QuestionType = Question.QuestionType

CHOICE_TYPES = (
    QuestionType.SINGLE_CHOICE,
    QuestionType.MULTIPLE_CHOICE,
    QuestionType.DROPDOWN,
)


def validate_json_object(value: Any) -> None:
    if not isinstance(value, dict):
        raise serializers.ValidationError("This field must be a JSON object.")


class SurveySerializer(serializers.ModelSerializer):
    workspace_id = serializers.PrimaryKeyRelatedField(
        source="workspace",
        queryset=Workspace.objects.all(),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Survey
        fields = [
            "id",
            "workspace_id",
            "title",
            "description",
            "status",
            "settings",
            "logic_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "settings": {"validators": [validate_json_object]},
            "logic_rules": {"validators": [validate_json_object]},
        }

    def validate_workspace_id(self, workspace: Workspace) -> Workspace:
        if self.instance is not None:
            if workspace.pk != self.instance.workspace_id:
                raise serializers.ValidationError(
                    "The workspace of a survey cannot be changed."
                )
            return workspace
        if workspace.owner.pk != self.context["request"].user.id:
            raise serializers.ValidationError(
                "You do not have permission to use this workspace."
            )
        return workspace


class SurveyListSerializer(serializers.ModelSerializer):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Survey
        fields = [
            "id",
            "workspace_id",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        Model = Question
        fields = [
            "id",
            "survey_id",
            "title",
            "description",
            "type",
            "is_required",
            "order",
            "properties",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "survey_id",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "properties": {"validators": [validate_json_object]},
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = self.instance
        if instance is not None and "type" not in attrs and "properties" not in attrs:
            return attrs

        question_type = attrs.get(
            "type", instance.type if instance else QuestionType.TEXT
        )
        properties = attrs.get("properties", instance.properties if instance else {})

        if question_type in CHOICE_TYPES:
            options = properties.get("options")
            if not isinstance(options, list) or not options:
                raise serializers.ValidationError(
                    {
                        "properties": (
                            "Choice questions require a non-empty'options' list."
                        )
                    }
                )
        elif question_type == QuestionType.RATING:
            low, high = properties.get("min"), properties.get("max")

            def is_int(value: Any) -> bool:
                return isinstance(value, int) and not isinstance(value, bool)

            if not (is_int(low) and is_int(high) and low < high):
                raise serializers.ValidationError(
                    {
                        "properties": (
                            "Rating questions require integer 'min' and 'max'"
                            "with min < max."
                        )
                    }
                )
        return attrs
