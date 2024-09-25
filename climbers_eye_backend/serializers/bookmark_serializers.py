from rest_framework import serializers
from climbers_eye_backend import models

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bookmark
        fields = '__all__'