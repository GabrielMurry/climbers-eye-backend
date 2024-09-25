from rest_framework import serializers
from climbers_eye_backend import models

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Like
        fields = '__all__'
