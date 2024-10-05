from django.urls import path
from .views import LogbookList

app_name = 'profile'

urlpatterns = [
    path('logbook_list/<int:spraywall_id>', LogbookList.as_view(), name='logbooklist'),
]