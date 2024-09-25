from rest_framework import serializers
from climbers_eye_backend import models

class GymSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Gym
        fields = '__all__'