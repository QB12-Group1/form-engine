from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from workspaces.models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Workspace
        fields = ["id", "owner", "name", "password", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().update(instance, validated_data)
