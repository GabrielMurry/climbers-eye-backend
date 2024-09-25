from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.middleware.csrf import get_token as get_csrf_token
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CustomTokenObtainPairSerializer, PersonSerializer

from rest_framework import status, generics, permissions

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class UserSignup(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = PersonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def temp_csrf_token(request):
    if request.method == 'GET':
        # retrieve token that will be the temp token
        token = get_csrf_token(request)
        # Store the token in the session
        request.session['csrf_token'] = token
        # Rotate the token for security (optional but recommended)
        # rotate_token(request)
        return Response({'csrfToken': token}, status=status.HTTP_200_OK)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            print(request.data['refresh'])
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_token(request):
    if request.method == 'POST':
        # Implementing secure token rotation
        current_refresh_token = request.data.get('currentRefreshToken')
        if current_refresh_token is None:
            return Response({'error': 'Refresh token is missing.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Create a RefreshToken object from the given refresh token string
            # Library internally validates the refresh token - checks if it has expired, has been tampered with, or is not a refresh token.
            # If an invalid refresh token is given (for instance, it has expired), catch TokenError and return 401 status code error

            # Decode the refresh token to get access to user details
            decoded_refresh_token = RefreshToken(current_refresh_token)
            user_id = decoded_refresh_token['user_id']  # Ensure your token has 'user_id' encoded

            # Retrieve the user
            User = get_user_model()
            user = User.objects.get(id=user_id)
            print('-+++++++')
            print(user)

            # Generate a new access token
            new_access_token = decoded_refresh_token.access_token

            # Generate a new refresh token with refreshed expiration - refresh token rotation
            # Better user experience so long as the user is active
            new_refresh_token = RefreshToken.for_user(user)
            new_refresh_token.set_exp(lifetime=timedelta(days=7))

            data = {
                'accessToken': str(new_access_token), # Return the new access token
                'refreshToken': str(new_refresh_token) # Return the new refresh token
            }
            return Response(data, status=status.HTTP_200_OK)
        except TokenError as e:
            # Handle invalid or expired token
            return Response({"error", str(e)}, status=status.HTTP_401_UNAUTHORIZED)
