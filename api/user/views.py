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
from .serializers import CustomTokenObtainPairSerializer, PersonSerializer, AppleAccountSerializer, GoogleAccountSerializer
from rest_framework.request import Request
import requests, jwt
from rest_framework import status, generics, permissions
import base64, uuid
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from .models import AppleAccount, Person, GoogleAccount
import environ
env = environ.Env()
environ.Env.read_env()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class UserSignup(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args, **kwargs):
        serializer = PersonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': serializer.data,
            'csrfToken': get_csrf_token(request),
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class CheckEmail(APIView):
    @staticmethod
    def email_exists(email: str):
        return Person.objects.filter(email=email).exists()

    def post(self, request: Request):
        email = request.data.get('email')
        if (self.email_exists(email)):
            return Response(data={'exists': True}, status=status.HTTP_200_OK)
        return Response(data={'exists': False}, status=status.HTTP_200_OK)

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
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            print(f'Error logging out: {e}')
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
        
def base64url_decode(val):
    val += '=' * (-len(val) % 4)  # add padding if missing
    return base64.urlsafe_b64decode(val)
        
def rsa_public_key_from_jwk(jwk):
    n = int.from_bytes(base64url_decode(jwk['n']), byteorder='big')
    e = int.from_bytes(base64url_decode(jwk['e']), byteorder='big')
    public_numbers = rsa.RSAPublicNumbers(e, n)
    return public_numbers.public_key(backend=default_backend())

def validate_identity_token(identity_token: str, provider_keys: list, issuer: str):
    try:
        unverified_header = jwt.get_unverified_header(identity_token)
        provider_key = None
        for key in provider_keys:
            if key['kid'] == unverified_header['kid']:
                provider_key = key
        if not provider_key:
            raise ValueError("Matching public key not found.")
        rsa_public_key = rsa_public_key_from_jwk(provider_key)
        # Decode and verify the identity token
        claims = jwt.decode(
            identity_token,
            rsa_public_key,
            algorithms=[provider_key['alg']],
            audience=env('GOOGLE_CLIENT_ID'),
            issuer=env('GOOGLE_ISSUER')
        )
        return claims
    except:
        print('Identity token validation error.')

def get_provider_keys(provider: str):
    match provider:
        case 'apple':
            return requests.get('https://appleid.apple.com/auth/keys').json()['keys']
        case 'google':
            return requests.get('https://www.googleapis.com/oauth2/v3/certs').json()['keys']
        case _:
            raise Exception("Get keys error. Invalid provider.")
        
def get_provider_issuer(provider: str):
    match provider:
        case 'apple':
            return env('APPLE_ISSUER')
        case 'google':
            return env('GOOGLE_ISSUER')
        case _:
            raise Exception("Get issuer error. Invalid provider.")

def generate_username(first_name: str, last_name: str):
    username = f"{first_name}{last_name}".replace(" ", "")
    if Person.objects.filter(username=username).exists():
        suffix = uuid.uuid4().hex[:6]
        return f"{username}{suffix}"
    else:
        return username

class AppleSignUp(APIView):
    serializer_class = PersonSerializer

    def get_user_from_apple_claims(self, claims):
        # Check if Apple user already exists
        apple_sub = claims.get('sub')
        try:
            apple_account = AppleAccount.objects.select_related('user').get(apple_sub=apple_sub)
            return apple_account.user
        except AppleAccount.DoesNotExist:
            return None
    
    def post(self, request: Request):
        # User clicked to sign in (sign up) with their apple account
        first_name = request.data.get('firstName')
        last_name = request.data.get('lastName')
        identity_token = request.data.get('identityToken')
        apple_keys = get_provider_keys('apple')
        issuer = get_provider_issuer('apple')
        claims = validate_identity_token(identity_token, apple_keys, issuer)

        user = self.get_user_from_apple_claims(claims)
        if user is None:
            # Save user
            user_data = {
                'username': generate_username(first_name, last_name),
                'email': claims.get('email'),
                'password': None,
            }
            user_serializer = PersonSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            # Save user apple account details
            apple_acc_data = {
                'user': user.id,
                'apple_sub': claims.get('sub'),
                'is_private_email': claims.get('is_private_email'),
                'real_user_status': claims.get('real_user_status')
            }
            apple_acc_serializer = AppleAccountSerializer(data=apple_acc_data)
            apple_acc_serializer.is_valid(raise_exception=True)
            apple_acc_serializer.save()
            # Send tokens and user data
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': user_serializer.data,
                'csrfToken': get_csrf_token(request),
                'refreshToken': str(refresh),
                'accessToken': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        else:
            # User already exists, send their data and tokens 
            user_data = PersonSerializer(user).data
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': user_data,
                'csrfToken': get_csrf_token(request),
                'refreshToken': str(refresh),
                'accessToken': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

class GoogleSignUp(APIView):
    permission_classes = [permissions.AllowAny]

    def get_user_from_google_claims(self, claims):
        # Check if Google user already exists
        google_sub = claims.get('sub')
        try:
            google_account = GoogleAccount.objects.select_related('user').get(google_sub=google_sub)
            return google_account.user
        except GoogleAccount.DoesNotExist:
            return None

    def post(self, request: Request):
        first_name = request.data.get('firstName')
        last_name = request.data.get('lastName')
        identity_token = request.data.get('identityToken')
        google_keys = get_provider_keys('google')
        issuer = get_provider_issuer('google')
        claims = validate_identity_token(identity_token, google_keys, issuer)
        user = self.get_user_from_google_claims(claims)
        if user is None:
            # Save user
            user_data = {
                'username': generate_username(first_name, last_name),
                'email': claims.get('email'),
                'password': None,
            }
            user_serializer = PersonSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            # Save user apple account details
            google_acc_data = {
                'user': user.id,
                'google_sub': claims.get('sub'),
            }
            google_acc_serializer = GoogleAccountSerializer(data=google_acc_data)
            google_acc_serializer.is_valid(raise_exception=True)
            google_acc_serializer.save()
            # Send tokens and user data
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': user_serializer.data,
                'csrfToken': get_csrf_token(request),
                'refreshToken': str(refresh),
                'accessToken': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        else:
            # User already exists, send their data and tokens 
            user_data = PersonSerializer(user).data
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': user_data,
                'csrfToken': get_csrf_token(request),
                'refreshToken': str(refresh),
                'accessToken': str(refresh.access_token),
            }, status=status.HTTP_200_OK)