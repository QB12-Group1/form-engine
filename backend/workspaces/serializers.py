from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from .models import Workspace

UserModel = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = UserModel
        fields = ["id", "full_name", "email"]

    def get_full_name(self, obj: AbstractUser) -> str:
        return obj.get_full_name()


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = UserSummarySerializer(read_only=True)
    password = serializers.CharField(
        write_only=True, required=False, allow_null=True, min_length=8, max_length=256
    )
    is_password_protected = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Workspace
        fields = [
            "id",
            "name",
            "owner",
            "password",
            "is_password_protected",
            "invite_token",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "invite_token", "created_at", "updated_at"]

    def get_is_password_protected(self, obj: Workspace) -> bool:
        return bool(obj.password)

    def create(self, validated_data: dict[str, Any]) -> Workspace:
        raw_password = validated_data.pop("password", None)
        validated_data["password"] = (
            make_password(raw_password) if raw_password else None
        )
        return super().create(validated_data)

    def update(self, instance: Workspace, validated_data: dict[str, Any]) -> Workspace:
        if "password" in validated_data:
            raw_password = validated_data["password"]
            validated_data["password"] = (
                make_password(raw_password) if raw_password else None
            )
        return super().update(instance, validated_data)


class JoinWorkspaceSerializer(serializers.Serializer):
    invite_token = serializers.UUIDField(required=True)
    password = serializers.CharField(required=False, allow_null=True, default=None)
