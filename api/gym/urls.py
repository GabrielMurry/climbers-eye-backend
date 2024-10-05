from django.urls import path
from .views import GymList, UserChooseGym, GymDetail

app_name = 'gym'

urlpatterns = [
    path('list/', GymList.as_view(), name='listgym'),
    path('user_choose_gym/', UserChooseGym.as_view(), name='userchoosegym'),
    path('detail/<int:pk>', GymDetail.as_view(), name='detailgym'),
]