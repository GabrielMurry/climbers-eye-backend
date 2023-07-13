"""
URL configuration for spray_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from spray_backend import views
from django.conf.urls.static import static
from django.conf import settings
from .views import csrf_token_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('csrf-token/', csrf_token_view, name='csrf_token'),
    path('login/', views.login_user),
    path('signup/', views.signup_user),
    path('logout/', views.logout_user),
    path('composite/', views.composite),
    path('add_gym/<int:user_id>', views.add_gym),
    path('home/<int:user_id>', views.home),
    path('list/<int:spraywall_id>/<int:user_id>', views.list),
    path('spraywall/', views.spraywall),
    path('add_boulder/<int:spraywall_id>/<int:user_id>', views.add_boulder),
    path('like_boulder/<int:boulder_id>/<int:user_id>', views.like_boulder),
    path('bookmark_boulder/<int:boulder_id>/<int:user_id>', views.bookmark_boulder),
    path('sent_boulder/<int:boulder_id>', views.sent_boulder),
    path('updated_boulder_data/<int:boulder_id>/<int:user_id>', views.updated_boulder_data),
    path('delete_boulder/<int:boulder_id>', views.delete_boulder),
    path('query_gyms/', views.query_gyms),
    path('queried_gym_spraywall/<int:gym_id>', views.queried_gym_spraywall),
    path('choose_gym/<int:user_id>/<int:gym_id>', views.choose_gym),
    path('profile/<int:user_id>/<int:spraywall_id>', views.profile),
    path('circuits/<int:user_id>/<int:spraywall_id>/<int:boulder_id>', views.circuits),
    path('delete_circuit/<int:user_id>/<int:spraywall_id>/<int:circuit_id>', views.delete_circuit),
    path('add_or_remove_boulder_in_circuit/<int:circuit_id>/<int:boulder_id>', views.add_or_remove_boulder_in_circuit),
    path('get_boulders_from_circuit/<int:user_id>/<int:circuit_id>', views.get_boulders_from_circuit),
    path('boulder_stats/<int:boulder_id>', views.boulder_stats),
    path('filter_circuits/<int:user_id>/<int:spraywall_id>', views.filter_circuits),
    path('add_profile_banner_image/<int:user_id>', views.add_profile_banner_image),
    path('add_new_spraywall/<int:gym_id>', views.add_new_spraywall),
    path('delete_spraywall/<int:spraywall_id>', views.delete_spraywall),
    path('edit_gym/<int:gym_id>', views.edit_gym),
    path('edit_spraywall/<int:spraywall_id>', views.edit_spraywall),
]

# serve those static image files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
