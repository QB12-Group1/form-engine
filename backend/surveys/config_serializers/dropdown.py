from rest_framework import serializers


class DropdownConfigSerializer(serializers.Serializer):
    options = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=False),
        min_length=2,
        allow_empty=False,
    )
    placeholder = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="Select an option",
    )
    allow_other = serializers.BooleanField(default=False)
