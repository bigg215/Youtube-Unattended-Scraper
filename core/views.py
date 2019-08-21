from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect, HttpResponse, reverse
from django.views.generic.base import View
from django.contrib import messages
from django.http import HttpResponseBadRequest

from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow, FlowExchangeError
from oauth2client.clientsecrets import loadfile
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage
from .models import CredentialsModel, User

import googleapiclient.discovery
import googleapiclient.errors
import json
import jsonpickle
import hashlib
import os

from dateutil import parser
import datetime

from django.views.generic import TemplateView

from pytube import YouTube

_CSRF_KEY = 'google_oauth2_csrf_token'
_FLOW_KEY = 'google_oauth2_flow_{0}'

def _create_flow(request, scopes, return_url=None):
	"""Creates flow object.

	Args:
		request: Django request object.
		scopes: YouTube request oauth2 scopes.
		return_url: Url to return to after flow object is created.

	Returns:
		oauth2 flow object that is stored in the session.

	"""
	#Loading client secrets from .json file, client_type has no current use
	_client_type, client_info = loadfile(settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON)

	#Generate CSRF token and store it in the session
	csrf_token = hashlib.sha256(os.urandom(1024)).hexdigest()

	request.session[_CSRF_KEY] = csrf_token

	state = json.dumps({
		'csrf_token': csrf_token,
		'return_url': return_url,
	})

	#Initialize flow object with client_info 
	flow = OAuth2WebServerFlow(
		client_id=client_info['client_id'],
		client_secret=client_info['client_secret'],
		scope=scopes,
		state=state,
		redirect_uri=client_info['redirect_uris'][0]
	)

	flow_key = _FLOW_KEY.format(csrf_token)
	request.session[flow_key] = jsonpickle.encode(flow)
	return flow

def _get_flow_for_token(csrf_token, request):
	""" Retrieves flow from session.
	
	Args:
		csrf_token: The token that is passed should match the previously
		generated one stored in the session.
	
	Returns:
		The oauth2 flow object based on the CSRF token.
	"""
	flow_pickle = request.session.get(_FLOW_KEY.format(csrf_token), None)
	return None if flow_pickle is None else jsonpickle.decode(flow_pickle)

def get_storage(request):
	""" Credential storage helper.

	Args:
		request: Django request object.
	
	Returns:
		Django storage helper for interacting with the credentials model.
	"""
	return DjangoORMStorage(CredentialsModel, 'id', request.user.id, 'credential')

def oauth2_authorize(request):
	""" Authorize view to start oauth2 flow.

	Args:
		request: Django request object.

	Returns:
		A redirect to Google oauth2 authorization or requested return url.
	"""
	return_url = request.GET.get('return_url', None)
	if not return_url:
		return_url = request.META.get('HTTP_REFERER', '/')

	scopes = 'https://www.googleapis.com/auth/youtube'

	if not request.user.is_authenticated:
		return redirect('login')
	else:
		credential = get_storage(request).get()
		if credential is None or credential.invalid == True:
			flow = _create_flow(request=request, scopes=scopes, return_url=return_url)
			authorize_url = flow.step1_get_authorize_url()
			return redirect(authorize_url)
	return redirect(return_url)

def oauth2_callback(request):
	""" Callback view that validates the user's return from oauth2 provider.
	
	Args:
		request: Django request object.

	Returns:
		A redirect to requested return url.
	"""
	if not request.user.is_authenticated:
		return HttpResponseBadRequest('User authorization failed')

	if 'error' in request.GET:
		reason = request.GET.get('error_description', request.GET.get('error', ''))
		reason = reason.escape(reason)
		return HttpResponseBadRequest(f'Authorization failed {reason}')

	try:
		encoded_state = request.GET['state']
		code = request.GET['code']
	except KeyError:
		return HttpResponseBadRequest('Request missing state or authorization code')

	try:
		server_csrf = request.session[_CSRF_KEY]
	except KeyError:
		return HttpResponseBadRequest('No existing session for this flow')

	try:
		state = json.loads(encoded_state)
		client_csrf = state['csrf_token']
		return_url = state['return_url']
	except (ValueError, KeyError):
		return HttpResponseBadRequest('Invalid state parameter')

	if client_csrf != server_csrf:
		return HttpResponseBadRequest('Invalid CSRF token')

	flow = _get_flow_for_token(client_csrf, request)

	if not flow:
		return HttpResponseBadRequest('Missing oauth2 flow')

	try:
		credentials = flow.step2_exchange(code)
	except FlowExchangeError as exchange_error:
		return HttpResponseBadRequest(f'An error has occurred: {exchange_error}')

	get_storage(request).put(credentials)

	return redirect(return_url)

class HomePageView(View):

	def get(self, request, *args, **kwargs):
		
		credentials = get_storage(request).get()

		youtube = googleapiclient.discovery.build(
			'youtube', 'v3', credentials=credentials)

		api_request = youtube.playlists().list(
			part="snippet,contentDetails",
			maxResults=25,
			mine=True,
		)

		response = api_request.execute()

		return render(request, 'core/home.html', {
			'response': response,
		})

def update_youtube_profile(request):
	user = get_object_or_404(User, pk=request.user.id)

	credentials = get_storage(request).get()

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
	credentials = get_storage(request).get()

	youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

	api_request = youtube.playlistItems().list(
		part="snippet",
		playlistId=playlist,
	)

	response = api_request.execute()

	return render(request, 'core/playlist.html', {
				'response': response,
			})

def video_details(request, video):

	yt = YouTube(f'http://youtube.com/watch?v={video}')

	return render(request, 'core/video.html', {
		'progressive': yt.streams.filter(progressive=True).order_by('resolution').desc().all(),
		'dash':  yt.streams.filter(adaptive=True, only_video=True).desc().all(),
		'audio': yt.streams.filter(only_audio=True).desc().all(),
		'video': video,
	})

def video_download(request, video, itag):

	yt = YouTube(f'http://youtube.com/watch?v={video}')
	yt.streams.get_by_itag(itag).download(settings.VIDEO_DIR)

	messages.success(request, f'Video with an ID of {video} and itag of {itag} downloaded successfully to {settings.VIDEO_DIR}')

	return redirect(reverse('core:home'))
