from django.urls import path
from .views import CircuitList, CircuitDetail

app_name = 'circuit'

urlpatterns = [
    path('api/circuit_list/<int:spraywall_id>', CircuitList.as_view(), name='listcircuit'),
    path('api/circuit/<int:pk>', CircuitDetail.as_view(), name='circuitdetail'),
]