from rest_framework import serializers
from .models import Engagement

class EngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engagement
        fields = '__all__'  # Includes all model fields in the API response

