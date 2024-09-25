from django.urls import path
from .views import BookmarkBoulder

app_name = 'bookmark'

urlpatterns = [
    path('api/bookmark_boulder/<int:boulder_id>/<int:user_id>', BookmarkBoulder.as_view(), name='bookmarkboulder'),
]