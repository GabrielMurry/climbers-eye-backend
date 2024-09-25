from django.urls import path
from .views import temp_csrf_token, update_token, CustomTokenObtainPairView, LogoutView, UserSignup

app_name = 'auth'

urlpatterns = [
    path('api/temp_csrf_token/', temp_csrf_token),
    path('api/update_token/', update_token),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/signup/', UserSignup.as_view(), name='signup'),
]