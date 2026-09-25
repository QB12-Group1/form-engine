from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import serializers

UserModel = get_user_model()


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        help_text="Google ID token obtained from Google OAuth."
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        token = attrs.get("id_token")

        try:
            id_info = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError as e:
            raise serializers.ValidationError(
                {"id_token": "Invalid or expired Google token."}
            ) from e

        email = id_info.get("email")
        if not email:
            raise serializers.ValidationError("Google token does not contain email.")

        if not id_info.get("email_verified", settings.DEBUG):
            raise serializers.ValidationError(
                {"id_token": "Google account email is not verified."}
            )

        attrs["user_info"] = {
            "email": email,
            "first_name": id_info.get("given_name", ""),
            "last_name": id_info.get("family_name", ""),
        }

        return attrs


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    email = serializers.EmailField()
