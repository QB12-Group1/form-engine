from typing import Any

from rest_framework import serializers


class TextConfigSerializer(serializers.Serializer):
    placeholder = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    min_length = serializers.IntegerField(
        required=False,
        min_value=0,
        allow_null=True,
        default=None,
    )
    max_length = serializers.IntegerField(
        required=False,
        min_value=1,
        allow_null=True,
        default=None,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        min_length = attrs.get("min_length")
        max_length = attrs.get("max_length")

        if (
            min_length is not None
            and max_length is not None
            and min_length > max_length
        ):
            raise serializers.ValidationError(
                "min_length cannot be greater than max_length."
            )

        return attrs
