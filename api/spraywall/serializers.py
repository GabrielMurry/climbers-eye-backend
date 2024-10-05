from rest_framework import serializers
from .models import SprayWall
from ..gym.models import Gym
from utils.fields import UrlField

class SprayWallSerializer(serializers.ModelSerializer):
    url = UrlField(source='image_url', required=True)
    width = serializers.CharField(source='image_width', required=True)
    height = serializers.CharField(source='image_height', required=True)
    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all())  # Use PrimaryKeyRelatedField

    class Meta:
        model = SprayWall
        fields = ['id', 'name', 'url', 'width', 'height', 'gym']