from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.AuthenticationURL.as_view(), name='spotify-auth'),
    path('redirect/', views.spotify_redirect, name='spotify-redirect'),
    path('check-auth/', views.CheckAuthentication.as_view(), name='check-auth'),
    path('playlist/<str:playlist_id>/tracks/', views.playlist_tracks, name='playlist-tracks'),
    path('playlist/<str:playlist_id>/convert/', views.convert_playlist, name='convert-playlist'),
    path('', views.spotify_interface, name='spotify-interface')
]