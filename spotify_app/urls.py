from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.AuthenticationURL.as_view(), name='spotify-auth'),
    path('redirect/', views.spotify_redirect, name='spotify-redirect'),
    path('check-auth/', views.CheckAuthentication.as_view(), name='check-auth'),
    path('', views.spotify_interface, name='spotify-interface')
]