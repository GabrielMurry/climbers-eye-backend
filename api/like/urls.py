from django.urls import path
from .views import LikeBoulder, LikeList

app_name = 'like'

urlpatterns = [
    path('list/<int:spraywall_id>', LikeList.as_view(), name='likelist'),
    path('<int:boulder_id>', LikeBoulder.as_view(), name='likeboulder'),
]