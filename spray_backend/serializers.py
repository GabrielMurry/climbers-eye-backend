from .models import Gym, SprayWall, Boulder
from rest_framework import serializers

class BoulderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Boulder
        fields = '__all__'

class SprayWallSerializer(serializers.ModelSerializer):
    boulders = BoulderSerializer(many=True, read_only=True)

    class Meta:
        model = SprayWall
        fields = '__all__'

class GymSerializer(serializers.ModelSerializer):
    spraywalls = SprayWallSerializer(many=True, read_only=True)

    class Meta:
        model = Gym
        fields = '__all__'
        