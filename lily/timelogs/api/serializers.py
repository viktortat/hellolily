import datetime

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from ..models import LOGGABLE_MODELS, TimeLog


class TimeLogSerializer(serializers.ModelSerializer):
    """
    Serializer for the TimeLog model.
    """
    # Show string versions of fields.
    user = serializers.StringRelatedField(read_only=True)
    gfk_content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.filter(model__in=LOGGABLE_MODELS),
        write_only=True,
    )
    gfk_object_id = serializers.IntegerField(write_only=True)
    date = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        user = self.context.get('request').user

        validated_data.update({
            'user': user,
        })

        if not validated_data.get('date'):
            validated_data.update({
                'date': datetime.datetime.now()
            })

        return super(TimeLogSerializer, self).create(validated_data)

    class Meta:
        model = TimeLog
        fields = (
            'id',
            'case',
            'date',
            'gfk_content_type',
            'gfk_object_id',
            'hours_logged',
            'user',
        )
