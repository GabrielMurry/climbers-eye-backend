from rest_framework import serializers
from climbers_eye_backend import models
from climbers_eye_backend.serializers.fields import UrlField

class SprayWallSerializer(serializers.ModelSerializer):
    url = UrlField(source='image_url', required=True)
    width = serializers.CharField(source='image_width', required=True)
    height = serializers.CharField(source='image_height', required=True)
    gym = serializers.PrimaryKeyRelatedField(queryset=models.Gym.objects.all())  # Use PrimaryKeyRelatedField

    class Meta:
        model = models.SprayWall
        fields = ['id', 'name', 'url', 'width', 'height', 'gym']