from django.urls import path
from .views import LogbookList, LikeList, BookmarkList, CreationList

app_name = 'profile'

urlpatterns = [
    path('logbook_list/<int:spraywall_id>', LogbookList.as_view(), name='logbooklist'),
    path('like_list/<int:spraywall_id>', LikeList.as_view(), name='likelist'),
    path('bookmark_list/<int:spraywall_id>', BookmarkList.as_view(), name='bookmarklist'),
    path('creation_list/<int:spraywall_id>', CreationList.as_view(), name='creationlist'),
]