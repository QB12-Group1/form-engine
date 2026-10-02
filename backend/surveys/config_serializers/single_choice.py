from rest_framework import serializers


class SingleChoiceConfigSerializer(serializers.Serializer):
    options = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=False),
        min_length=2,
        allow_empty=False,
    )
    allow_other = serializers.BooleanField(default=False)
