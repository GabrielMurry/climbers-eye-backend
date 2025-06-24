from rest_framework import serializers
from .models import SprayWall
from ..gym.models import Gym
from utils.fields import UrlField

class SprayWallSerializer(serializers.ModelSerializer):
    url = UrlField(source='image_url', required=True, label='spraywall_image') # label is for identifying which prefix (folder) this image should go under in s3 bucket.
    width = serializers.CharField(source='image_width', required=True)
    height = serializers.CharField(source='image_height', required=True)
    thumbnailUrl = UrlField(source='thumbnail_image_url', required=True, label='thumbnail_spraywall_image')
    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all())  # Use PrimaryKeyRelatedField

    class Meta:
        model = SprayWall
        fields = ['id', 'name', 'url', 'width', 'height', 'thumbnailUrl', 'gym']