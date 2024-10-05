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

from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.user.urls', namespace='user')),
    path('boulder/', include('api.boulder.urls', namespace='boulder')),
    path('gym/', include('api.gym.urls', namespace='gym')),
    path('circuit/', include('api.circuit.urls', namespace='circuit')),
    path('spraywall/', include('api.spraywall.urls', namespace='spraywall')),
    path('like/', include('api.like.urls', namespace='like')),
    path('bookmark/', include('api.bookmark.urls', namespace='bookmark')),
    path('send/', include('api.send.urls', namespace='send')),
    path('profile/', include('api.profile.urls', namespace='profile')),
] 