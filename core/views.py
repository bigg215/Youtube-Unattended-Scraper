from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect, HttpResponse
from django.views.generic.base import View

from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel, User

import googleapiclient.discovery
import googleapiclient.errors
import json

from dateutil import parser
import datetime

from django.views.generic import TemplateView

flow = flow_from_clientsecrets(
			settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
			scope='https://www.googleapis.com/auth/youtube',
			redirect_uri='http://localhost:8000/core/auth/')

class HomePageView(View):
    
    def get(self, request, *args, **kwargs):
    	storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
    	credentials = storage.get()

    	youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

    	api_request = youtube.playlists().list(
        	part="snippet,contentDetails",
        	maxResults=25,
        	mine=True
    	)

    	response = api_request.execute()

    	return render(request, 'core/home.html', {
				'response': response,
			})

class AuthorizeView(View):

	def get(self, request, *args, **kwargs):

		if not request.user.is_authenticated:
			return redirect('/')
		else:
			storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
			credential = storage.get()
			
			if credential is None or credential.invalid == True:
				flow.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, request.user)
				authorize_url = flow.step1_get_authorize_url()
				return redirect(authorize_url)
			return redirect('/core')

class AuthCallbackView(View):

	def get(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return redirect('/')
		else:
			if not xsrfutil.validate_token(
				settings.SECRET_KEY, request.GET.get('state').encode(),
				request.user):
				return HttpResponseBadRequest()
			credential = flow.step2_exchange(request.GET)
			storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
			storage.put(credential)
			return redirect('/core')

def update_youtube_profile(request):
	user = get_object_or_404(User, pk=request.user.id)

	storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
	credentials = storage.get()

	youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

	api_request = youtube.channels().list(part="snippet", mine=True)

	response = api_request.execute()
	
	user.youtubeprofile.channel_id = response['items'][0]['id']
	user.youtubeprofile.channel_title = response['items'][0]['snippet']['title']
	user.youtubeprofile.description = response['items'][0]['snippet']['description']
	user.youtubeprofile.thumbnail_uri = response['items'][0]['snippet']['thumbnails']['default']['url']

	dt = parser.parse(response['items'][0]['snippet']['publishedAt'])
	user.youtubeprofile.publish_date = dt.strftime("%Y-%m-%d")
	user.save()

	return redirect('/core')

def playlist_details(request, playlist):
	storage = DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')
	credentials = storage.get()

	youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

	api_request = youtube.playlistItems().list(
	    part="snippet",
	    playlistId=playlist,
	)

	response = api_request.execute()

	return render(request, 'core/playlist.html', {
				'response': response,
			})