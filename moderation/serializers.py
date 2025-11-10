from rest_framework import serializers


class TextModerationRequestSerializer(serializers.Serializer):
	email = serializers.EmailField()
	text = serializers.CharField(max_length=20000, allow_blank=False)


class ImageModerationRequestSerializer(serializers.Serializer):
	email = serializers.EmailField()
	image = serializers.ImageField()


class ModerationResultSerializer(serializers.Serializer):
	request_id = serializers.IntegerField()
	classification = serializers.CharField()
	confidence = serializers.FloatField()
	reasoning = serializers.CharField(allow_blank=True)


class AnalyticsSummarySerializer(serializers.Serializer):
	user = serializers.EmailField()
	counts = serializers.DictField(child=serializers.IntegerField())


