from typing import Any

from rest_framework import serializers

from workspaces.models import Workspace

from .models import Survey


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
    workspace_id = serializers.IntegerField(read_only=True)

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
