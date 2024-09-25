from django.urls import path
from .views import SpraywallList, SpraywallDetail

app_name = 'spraywall'

urlpatterns = [
    path('api/spraywall_list/<int:gym_id>', SpraywallList.as_view(), name='listspraywall'),
    path('api/spraywall/<int:pk>', SpraywallDetail.as_view(), name='detailspraywall'),
]