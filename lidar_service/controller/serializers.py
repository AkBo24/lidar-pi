from rest_framework import serializers
from .models import LidarFile

class LidarFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LidarFile
        fields = ['id', 'filename', 'file', 'uploaded_at']
