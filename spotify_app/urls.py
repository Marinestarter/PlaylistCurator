from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('login/', views.spotify_login, name='spotify_login'),  # Added name here
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('', views.spotify_interface, name='spotify_interface')
]