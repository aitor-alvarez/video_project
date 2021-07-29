from .models import *
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from utils.utils import *
from django.core.files.storage import default_storage
from django.http import JsonResponse
from botocore.exceptions import ClientError
import logging

@login_required
def showcase_videos(request):
	videos = Video.objects.filter(is_showcase=True)
	return render(request, 'videos/home.html', {'videos': videos})


@login_required
def upload_video(request):
	if request.method == 'POST':
		video_file = request.FILES.get('file', '')
		lang = request.POST.get('language', '')
		try:
			s3_response = s3_upload_file_to_bucket(video_file, 'videos-techcenter')
			audio_file = extract_audio_from_video(video_file)
			if audio_file is not None:
				del video_file
				file_url = upload_to_gcs(audio_file, 'flagship-videos')
				speech_txt = process_speech_to_txt(file_url, lang)
				vtt_obj = generate_vtt_caption(speech_txt)

		except ClientError as e:
			logging.error(e)
			return False






