from django.urls import path
from .views import GymList, UserChooseGym, GymDetail

app_name = 'gym'

urlpatterns = [
    path('api/gym_list/', GymList.as_view(), name='listgym'),
    path('api/user_choose_gym/', UserChooseGym.as_view(), name='userchoosegym'),
    path('api/gym/<int:pk>', GymDetail.as_view(), name='detailgym'),
]