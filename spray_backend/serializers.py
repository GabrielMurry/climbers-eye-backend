from .models import Gym, SprayWall, Boulder, Person, Send, Like, Circuit, Bookmark, Activity
from rest_framework import serializers

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

class SendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Send
        fields = '__all__'

class CircuitSerializer(serializers.ModelSerializer):
    boulders = serializers.PrimaryKeyRelatedField(many=True, queryset=Boulder.objects.all())

    class Meta:
        model = Circuit
        fields = '__all__'

class PersonSerializer(serializers.ModelSerializer):
    # A person can have many likes, bookmarks, and sends
    likes = LikeSerializer(many=True, read_only=True)
    bookmarks = BookmarkSerializer(many=True, read_only=True)
    sends = SendSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = '__all__'

class BoulderSerializer(serializers.ModelSerializer):
    # A boulder can have many persons
    persons = PersonSerializer(many=True, read_only=True)

    class Meta:
        model = Boulder
        fields = '__all__'

class SprayWallSerializer(serializers.ModelSerializer):
    # A spray wall can have many boulders
    boulders = BoulderSerializer(many=True, read_only=True)

    class Meta:
        model = SprayWall
        fields = '__all__'

class GymSerializer(serializers.ModelSerializer):
    # A gym can have many spray walls
    spraywalls = SprayWallSerializer(many=True, read_only=True)

    class Meta:
        model = Gym
        fields = '__all__'