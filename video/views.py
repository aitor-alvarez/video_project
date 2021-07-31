from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from utils.utils import *
from django.http import JsonResponse
from botocore.exceptions import ClientError
import logging
from .models import *
from django.views.generic.edit import FormView
from .forms import VideoForm
from django.http import HttpResponse


@login_required
def showcase_videos(request):
	videos = Video.objects.filter(is_showcase=True)
	return render(request, 'videos/home.html', {'videos': videos})


def video_upload_view(request):
	form = VideoForm()
	profile = Profile.objects.get(user=request.user)
	if profile is not None and Program.objects.filter(students__in=[profile]).exists():
		program = Program.objects.filter(students__in=[profile])
		return render(request, 'videos/upload_video.html', {"form": form, 'program': program})
	else:
		return render(request, 'videos/upload_video.html', {"error": 'Your user is not associated with a program.'})


def upload_form_ajax(request):
		form = VideoForm()
		if request.is_ajax and request.method == "POST":
			# get the form data
			form = VideoForm(request.POST)
			instance = form
			if form.is_valid():
				instance = form.save(commit=False)
				print(instance['video_file'])
				print(instance['language'])
			try:
				video_file = instance['video_file']
				s3_response = s3_upload_file_to_bucket(video_file, 'videos-techcenter')
				print(s3_response)
				instance['url'] = s3_response
				audio_file = extract_audio_from_video(video_file)
				if audio_file is not None:
					file_url = upload_to_gcs(audio_file, 'flagship-videos')
					speech_txt = process_speech_to_txt(file_url, instance['language'])
					vtt_obj = generate_vtt_caption(speech_txt)
					return JsonResponse()

			except ClientError as e:
				return JsonResponse({'error': e})








