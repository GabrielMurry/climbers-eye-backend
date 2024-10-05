from django.urls import path
from .views import SpraywallList, SpraywallDetail

app_name = 'spraywall'

urlpatterns = [
    path('list/<int:gym_id>', SpraywallList.as_view(), name='listspraywall'),
    path('detail/<int:pk>', SpraywallDetail.as_view(), name='detailspraywall'),
]