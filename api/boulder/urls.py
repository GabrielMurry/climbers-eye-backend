from django.urls import path
from .views import BoulderList, BoulderDetail, CompositeBoulderImage, BoulderInCircuit

app_name = 'boulder'

urlpatterns = [
    path('list/<int:spraywall_id>', BoulderList.as_view(), name='listboulder'),
    path('detail/<int:pk>', BoulderDetail.as_view(), name='boulderdetail'),
    path('composite/', CompositeBoulderImage.as_view(), name='compositeboulderimage'),
    path('boulder_in_circuit/<int:circuit_id>/<int:boulder_id>', BoulderInCircuit.as_view(), name='boulderincircuit'),
]