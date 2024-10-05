from django.urls import path
from .views import LikeBoulder

app_name = 'like'

urlpatterns = [
    path('<int:boulder_id>/<int:user_id>', LikeBoulder.as_view(), name='likeboulder'),
]