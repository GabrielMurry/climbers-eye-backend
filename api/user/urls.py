from django.urls import path
from .views import temp_csrf_token, update_token, CustomTokenObtainPairView, LogoutView, UserSignup

app_name = 'user'

urlpatterns = [
    path('temp_csrf_token/', temp_csrf_token),
    path('update_token/', update_token),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', UserSignup.as_view(), name='signup'),
]