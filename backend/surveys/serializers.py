from rest_framework import serializers

from workspaces.serializers import WorkspaceSerializer

from .models import Survey


class SurveySerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    settings = serializers.DictField(required=False, default=dict, allow_null=False)
    logic_rules = serializers.DictField(required=False, default=dict, allow_null=False)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Survey
        fields = [
            "id",
            "workspace",
            "title",
            "description",
            "status",
            "settings",
            "logic_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]
