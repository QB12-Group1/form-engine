from typing import Any

from rest_framework import serializers


class RatingConfigSerializer(serializers.Serializer):
    min_value = serializers.IntegerField(default=1)
    max_value = serializers.IntegerField(default=5)
    min_label = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )
    max_label = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = getattr(self, "instance", None)

        min_val = attrs.get("min_value", getattr(instance, "min_value", None))
        max_val = attrs.get("max_value", getattr(instance, "max_value", None))

        if min_val is not None and max_val is not None and min_val >= max_val:
            raise serializers.ValidationError(
                {"max_value": "max_value must be strictly greater than min_value."}
            )

        return attrs
