from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Shape the frontend expects:
      { id, type, is_read, created_at, data }
    """
    class Meta:
        model = Notification
        fields = ["id", "type", "is_read", "created_at", "data"]
