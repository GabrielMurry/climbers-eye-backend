from django.urls import path
from .views import SendList, SendDetail

app_name = 'send'

urlpatterns = [
    path('api/send_list/<int:boulder_id>', SendList.as_view(), name='listsend'),
    path('api/send/<int:pk>', SendDetail.as_view(), name='detailsend'),
]