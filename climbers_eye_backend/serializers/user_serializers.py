from rest_framework import serializers
from climbers_eye_backend.models import Person, Gym, Send, Like, Bookmark, Boulder
from climbers_eye_backend.serializers import spraywall_serializers
from django.contrib.auth.hashers import make_password

class PersonSerializer(serializers.ModelSerializer):
    profilePicUrl = serializers.CharField(source='image_url', read_only=True)
    profilePicWidth = serializers.CharField(source='image_width', read_only=True)
    profilePicHeight = serializers.CharField(source='image_height', read_only=True)
    logbookCount = serializers.SerializerMethodField(read_only=True)
    likesCount = serializers.SerializerMethodField(read_only=True)
    bookmarksCount = serializers.SerializerMethodField(read_only=True)
    creationsCount = serializers.SerializerMethodField(read_only=True)
    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all(), required=False, allow_null=True)
    spraywalls = spraywall_serializers.SprayWallSerializer(many=True, source='gym.spraywall_set', required=False, allow_null=True)

    class Meta:
        model = Person
        fields = ['id', 'username', 'name', 'email', 'profilePicUrl', 
                  'profilePicWidth', 'profilePicHeight', 'gym', 'spraywalls', 'logbookCount', 'likesCount',
                  'bookmarksCount', 'creationsCount']
        
    # Gym data response. Could also do this instead: gym_details = GymSerializer(source='gym', read_only=True)
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        gym_instance = instance.gym
        if gym_instance:
            representation['gym'] = {
                'id': gym_instance.id,
                'name': gym_instance.name,
                'address': gym_instance.address,
                'latitude': gym_instance.latitude,
                'longitude': gym_instance.longitude,
                'type': gym_instance.type
            }
            # Handle spraywalls if gym exists
            representation['spraywalls'] = spraywall_serializers.SprayWallSerializer(gym_instance.spraywall_set, many=True).data
        else:
            representation['gym'] = None  # No gym assigned
            representation['spraywalls'] = []  # No spraywalls since no gym
        return representation
    
    def get_logbookCount(self, obj: Person):
        return Send.objects.filter(person=obj).count()
    
    def get_likesCount(self, obj: Person):
        return Like.objects.filter(person=obj).count()
    
    def get_bookmarksCount(self, obj: Person):
        return Bookmark.objects.filter(person=obj).count()
    
    def get_creationsCount(self, obj: Person):
        return Boulder.objects.filter(setter=obj).count()