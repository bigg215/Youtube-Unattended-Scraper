# core/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.display_home, name='home'),
    path('authorize/', views.oauth2_authorize, name='authorize'),
    path('auth/', views.oauth2_callback, name='authcallback'),
    path('updateprofile/', views.update_youtube_profile, name='updateprofile'),
    path('playlists/<str:playlist>', views.playlist_details, name="playlistdetails"),
    path('video/<str:video>', views.video_details, name="videodetails"),
    path('video/<str:video>/<int:itag>', views.video_download, name="videodownload"),
]