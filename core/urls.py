# core/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.dashboard, name='home'),
    path('poll_state/', views.video_download_state, name="downloadstate"),
    path('authorize/', views.oauth2_authorize, name='authorize'),
    path('auth/', views.oauth2_callback, name='authcallback'),
    path('updateprofile/', views.update_youtube_profile, name='updateprofile'),
    path('playlists/', views.playlists_list, name="listplaylists"),
    path('playlists/<str:playlist>/', views.playlist_details, name="playlistdetails"),
    path('vtag/', views.tag_video, name="tagvideo"),
    path('vtag/delete/', views.tag_video, name="untagvideo"),
    path('video/<str:video>/', views.video_details, name="videodetails"),
    path('video/<str:video>/<int:itag>/', views.video_download, name="videodownload"),
]