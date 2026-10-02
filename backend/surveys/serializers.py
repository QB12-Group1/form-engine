from typing import Any

from rest_framework import serializers

from workspaces.serializers import WorkspaceSerializer

from . import config_serializers
from .models import Question, Survey


class SurveySerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    settings = serializers.DictField(required=False, default=dict, allow_null=False)
    logic_rules = serializers.DictField(required=False, default=dict, allow_null=False)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Survey
        fields = "__all__"
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class QuestionSerializer(serializers.ModelSerializer):
    survey = SurveySerializer(read_only=True)
    properties = serializers.DictField(required=False, default=dict, allow_null=False)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Question
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    CONFIG_SERIALIZERS = {
        "text": config_serializers.TextConfigSerializer,
        "singleChoice": config_serializers.SingleChoiceConfigSerializer,
        "multipleChoice": config_serializers.MultipleChoiceConfigSerializer,
        "dropdown": config_serializers.DropdownConfigSerializer,
        "rating": config_serializers.RatingConfigSerializer,
    }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        question_type = attrs.get("type")

        if question_type is None and self.instance:
            question_type = self.instance.type

        properties = attrs.get("properties")
        if properties is None:
            if self.instance is not None:
                return attrs
            properties = {}

        if not question_type or question_type not in self.CONFIG_SERIALIZERS:
            raise serializers.ValidationError({"type": "Unsupported question type."})

        if not question_type or question_type not in self.CONFIG_SERIALIZERS:
            raise serializers.ValidationError({"type": "Unsupported question type."})

        config_serializer_class = self.CONFIG_SERIALIZERS[question_type]

        config_serializer = config_serializer_class(data=properties)
        config_serializer.is_valid(raise_exception=True)
        attrs["properties"] = config_serializer.validated_data
        return attrs


class QuestionReorderSerializer(serializers.Serializer):
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Ordered list of question IDs matching the desired sequence.",
    )
