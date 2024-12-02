from django.urls import path
from . import views
urlpatterns = [
    path('auth/', views.YouTubeAuthURL.as_view(), name='youtube-auth'),
    path('redirect/', views.youtube_redirect, name='youtube-redirect'),
    path('', views.youtube_interface, name='youtube-interface')
]