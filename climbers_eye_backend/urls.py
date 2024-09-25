"""
URL configuration for climbers_eye project.

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
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from climbers_eye_backend.views import auth, boulder, circuit, gym, spraywall

urlpatterns = [
    path('api/list/<int:spraywall_id>', boulder.BoulderList.as_view(), name='listboulder'),
    path('api/boulder/<int:pk>', boulder.BoulderDetail.as_view(), name='boulderdetail'),
    path('api/like_boulder/<int:boulder_id>/<int:user_id>', boulder.LikeBoulder.as_view(), name='likeboulder'),
    path('api/bookmark_boulder/<int:boulder_id>/<int:user_id>', boulder.BookmarkBoulder.as_view(), name='bookmarkboulder'),
    path('api/send_list/<int:boulder_id>', boulder.SendList.as_view(), name='listsend'),
    path('api/send/<int:pk>', boulder.SendDetail.as_view(), name='detailsend'),
    path('api/composite/', boulder.CompositeBoulderImage.as_view(), name='compositeboulderimage'),
    path('api/gym_list/', gym.GymList.as_view(), name='listgym'),
    path('api/spraywall_list/<int:gym_id>', spraywall.SpraywallList.as_view(), name='listspraywall'),
    path('api/user_choose_gym/', gym.UserChooseGym.as_view(), name='userchoosegym'),
    path('api/circuit_list/<int:spraywall_id>', circuit.CircuitList.as_view(), name='listcircuit'),
    path('api/boulder_in_circuit/<int:circuit_id>/<int:boulder_id>', boulder.BoulderInCircuit.as_view(), name='boulderincircuit'),
    path('api/circuit/<int:pk>', circuit.CircuitDetail.as_view(), name='circuitdetail'),
    path('api/gym/<int:pk>', gym.GymDetail.as_view(), name='detailgym'),
    path('api/spraywall/<int:pk>', spraywall.SpraywallDetail.as_view(), name='detailspraywall'),
    path('api/temp_csrf_token/', auth.temp_csrf_token), # auth
    path('api/update_token/', auth.update_token), # auth
    path('api/login/', auth.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/logout/', auth.LogoutView.as_view(), name='logout'),
    path('api/signup/', auth.UserSignup.as_view(), name='signup'),
]

# boulder/urls.py...
# from django.urls import path
# from . import views

# app_name = 'boulder'

# urlpatterns = [
#     path('list/<int:spraywall_id>/', views.BoulderList.as_view(), name='list'),
#     path('<int:pk>/', views.BoulderDetail.as_view(), name='detail'),
#     path('like/<int:boulder_id>/<int:user_id>/', views.LikeBoulder.as_view(), name='like'),
#     path('bookmark/<int:boulder_id>/<int:user_id>/', views.BookmarkBoulder.as_view(), name='bookmark'),
#     path('send_list/<int:boulder_id>/', views.SendList.as_view(), name='list_send'),
#     path('send/<int:pk>/', views.SendDetail.as_view(), name='detail_send'),
#     path('composite/', views.CompositeBoulderImage.as_view(), name='composite_image'),
#     path('in_circuit/<int:circuit_id>/<int:boulder_id>/', views.BoulderInCircuit.as_view(), name='in_circuit'),
# ]


# urls.py...
# from django.urls import path, include
# from django.conf.urls.static import static
# from django.conf import settings

# urlpatterns = [
#     path('api/boulders/', include('boulder.urls', namespace='boulder')),
#     path('api/gyms/', include('gym.urls', namespace='gym')),
#     path('api/circuits/', include('circuit.urls', namespace='circuit')),
#     path('api/spraywalls/', include('spraywall.urls', namespace='spraywall')),
#     path('api/auth/', include('auth.urls', namespace='auth')),
# ]