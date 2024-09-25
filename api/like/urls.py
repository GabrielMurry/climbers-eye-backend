from django.urls import path
from .views import LikeBoulder

app_name = 'like'

urlpatterns = [
    path('api/like_boulder/<int:boulder_id>/<int:user_id>', LikeBoulder.as_view(), name='likeboulder'),
]