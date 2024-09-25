from django.urls import path
from .views import BoulderList, BoulderDetail, LikeBoulder, BookmarkBoulder, SendList, SendDetail, CompositeBoulderImage, BoulderInCircuit

app_name = 'boulder'

urlpatterns = [
    path('api/list/<int:spraywall_id>', BoulderList.as_view(), name='listboulder'),
    path('api/boulder/<int:pk>', BoulderDetail.as_view(), name='boulderdetail'),
    path('api/composite/', CompositeBoulderImage.as_view(), name='compositeboulderimage'),
    path('api/boulder_in_circuit/<int:circuit_id>/<int:boulder_id>', BoulderInCircuit.as_view(), name='boulderincircuit'),
]