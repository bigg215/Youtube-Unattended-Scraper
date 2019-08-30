from django.db import models
from oauth2client.contrib.django_util.models import CredentialsField
from django.contrib.auth.models import User

from django.db.models.signals import post_save
from django.dispatch import receiver

class VideoModel(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	video_id = models.CharField(max_length=50)
	title = models.CharField(max_length=100, blank=True)
	thumbnail_uri = models.URLField(blank=True)

	class Meta:
		unique_together = ['user', 'video_id']

class CredentialsModel(models.Model):
    credential = CredentialsField()

class YoutubeProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	channel_id = models.CharField(max_length=50, blank=True)
	channel_title = models.CharField(max_length=100, blank=True)
	description = models.TextField(max_length=500, blank=True)
	thumbnail_uri = models.CharField(max_length=200, blank=True)
	publish_date = models.DateField('date published', null=True, blank=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		YoutubeProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.youtubeprofile.save()
