from rest_framework import serializers


class MultipleChoiceConfigSerializer(serializers.Serializer):
    options = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=False),
        min_length=2,
        allow_empty=False,
    )
    min_selections = serializers.IntegerField(
        required=False,
        min_value=0,
        default=0,
    )
    max_selections = serializers.IntegerField(
        required=False,
        min_value=1,
        allow_null=True,
        default=None,
    )
    allow_other = serializers.BooleanField(default=False)

    def validate(self, attrs):
        options = attrs["options"]
        min_selections = attrs.get("min_selections", 0)
        max_selections = attrs.get("max_selections")

        if max_selections is not None:
            if max_selections > len(options):
                raise serializers.ValidationError(
                    {
                        "max_selections": (
                            "max_selections cannot be greater than "
                            "the number of options."
                        )
                    }
                )

            if min_selections > max_selections:
                raise serializers.ValidationError(
                    {
                        "min_selections": (
                            "min_selections cannot be greater than max_selections."
                        )
                    }
                )

        return attrs
