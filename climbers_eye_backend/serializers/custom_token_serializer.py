from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from climbers_eye_backend.models import Person, Like
from climbers_eye_backend.serializers import user_serializers
from django.middleware.csrf import get_token as get_csrf_token

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
        # Authenticate (validate) the user with username and password in 'attrs'
        # This parent validate function will then call our get_token custom class method
        jwt_user_tokens = super().validate(attrs)
        # Retrieve additional user data from the database
        person = Person.objects.get(username=self.user)
        # Use PersonSerializer to serialize user data
        user_data = user_serializers.PersonSerializer(person).data

        return {
            'user': user_data,
            'csrfToken': get_csrf_token(self.context['request']),
            'accessToken': jwt_user_tokens['access'],
            'refreshToken': jwt_user_tokens['refresh'],
        }