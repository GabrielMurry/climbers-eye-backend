from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.middleware.csrf import get_token as get_csrf_token
from .models import Person
from ..boulder.models import Boulder
from ..gym.models import Gym
from ..like.models import Like
from ..send.models import Send
from ..bookmark.models import Bookmark
from ..spraywall.serializers import SprayWallSerializer

class PersonSerializer(serializers.ModelSerializer):
    profilePicUrl = serializers.CharField(source='image_url', read_only=True)
    profilePicWidth = serializers.CharField(source='image_width', read_only=True)
    profilePicHeight = serializers.CharField(source='image_height', read_only=True)
    # logbookCount = serializers.SerializerMethodField(read_only=True)
    # likesCount = serializers.SerializerMethodField(read_only=True)
    # bookmarksCount = serializers.SerializerMethodField(read_only=True)
    # creationsCount = serializers.SerializerMethodField(read_only=True)
    gym = serializers.PrimaryKeyRelatedField(queryset=Gym.objects.all(), required=False, allow_null=True)
    spraywalls = SprayWallSerializer(many=True, source='gym.spraywall_set', required=False, allow_null=True)

    class Meta:
        model = Person
        fields = ['id', 'username', 'name', 'email', 'profilePicUrl', 
                  'profilePicWidth', 'profilePicHeight', 'gym', 'spraywalls']
        
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
            representation['spraywalls'] = SprayWallSerializer(gym_instance.spraywall_set, many=True).data
        else:
            representation['gym'] = None  # No gym assigned
            representation['spraywalls'] = []  # No spraywalls since no gym
        return representation
    
    # def get_logbookCount(self, obj: Person):
    #     return Send.objects.filter(person=obj).count()
    
    # def get_likesCount(self, obj: Person):
    #     return Like.objects.filter(person=obj).count()
    
    # def get_bookmarksCount(self, obj: Person):
    #     return Bookmark.objects.filter(person=obj).count()
    
    # def get_creationsCount(self, obj: Person):
    #     return Boulder.objects.filter(setter=obj).count()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # get token is parent function. returns the refresh token, giving it to validate() parent function will make the access token from it
        token = super().get_token(user)
        # Additional custom claims for the token
        token['email'] = user.email
        token['username'] = user.username
        return token

    def validate(self, attrs):
        try:
            # Authenticate (validate) the user with username and password in 'attrs'
            # This parent validate function will then call our get_token custom class method
            jwt_user_tokens = super().validate(attrs)
        except Exception as e:
            print(f'Error during validation: {e}')
            raise e  # Re-raise the exception after logging it

        # Retrieve additional user data from the database
        try:
            person = Person.objects.get(username=self.user)
            # Use PersonSerializer to serialize user data
            user_data = PersonSerializer(person).data
        except Person.DoesNotExist:
            print('Person not found')
            raise serializers.ValidationError('User not found')

        return {
            'user': user_data,
            'csrfToken': get_csrf_token(self.context['request']),
            'accessToken': jwt_user_tokens['access'],
            'refreshToken': jwt_user_tokens['refresh'],
        }