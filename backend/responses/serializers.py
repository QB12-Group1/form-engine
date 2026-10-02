from typing import Any

from rest_framework import serializers

from surveys.models import Question, Survey

from .models import Answer, ResponseSession


class ResponseSessionSerializer(serializers.ModelSerializer):
    survey_id = serializers.PrimaryKeyRelatedField(
        source="survey",
        queryset=Survey.objects.all(),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = ResponseSession
        fields = [
            "id",
            "survey_id",
            "respondent_ip",
            "user_agent",
            "is_completed",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "respondent_ip",
            "user_agent",
            "is_completed",
            "submitted_at",
            "created_at",
            "updated_at",
        ]


class AnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.PrimaryKeyRelatedField(
        source="question",
        queryset=Question.objects.all(),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Answer
        fields = [
            "id",
            "question_id",
            "session_id",
            "value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "session_id", "created_at", "updated_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        question = attrs["question"]
        session = self.context["session"]

        if question.survey_id != session.survey_id:
            raise serializers.ValidationError(
                "Question does not belong to this session's survey."
            )

        if session.is_completed:
            raise serializers.ValidationError("This response is already completed.")

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Answer:
        answer, _ = Answer.objects.update_or_create(
            question=validated_data["question"],
            session=self.context["session"],
            defaults={"value": validated_data["value"]},
        )

        return answer
