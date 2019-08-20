# core/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('authorize/', views.AuthorizeView.as_view(), name='authorize'),
    path('auth/', views.AuthCallbackView.as_view(), name='authcallback'),
    path('updateprofile/', views.update_youtube_profile, name='updateprofile'),
    path('playlists/<str:playlist>', views.playlist_details, name="playlistdetails"),
]