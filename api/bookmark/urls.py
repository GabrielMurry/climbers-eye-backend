from django.urls import path
from .views import BookmarkBoulder

app_name = 'bookmark'

urlpatterns = [
    path('<int:boulder_id>', BookmarkBoulder.as_view(), name='bookmarkboulder'),
]