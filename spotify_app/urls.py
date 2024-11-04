from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),

    path('login/', views.spotify_login),
    path('callback/', views.spotify_callback),
    path('', views.spotify_interface)
]