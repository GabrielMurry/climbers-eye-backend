from django.urls import path
from .views import CircuitList, CircuitDetail

app_name = 'circuit'

urlpatterns = [
    path('list/<int:spraywall_id>', CircuitList.as_view(), name='listcircuit'),
    path('detail/<int:pk>', CircuitDetail.as_view(), name='circuitdetail'),
]