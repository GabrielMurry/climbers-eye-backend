from django.urls import path
from .views import SendList, SendDetail, SendLogbookList

app_name = 'send'

urlpatterns = [
    path('logbook_list/<int:spraywall_id>', SendLogbookList.as_view(), name='listlogbook'),
    path('list/<int:boulder_id>', SendList.as_view(), name='listsend'),
    path('detail/<int:pk>', SendDetail.as_view(), name='detailsend'),
]