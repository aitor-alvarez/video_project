from .models import *
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from utils.utils import *


@login_required
def showcase_videos(request):
	videos = Video.objects.filter(is_showcase=True)
	return render(request, 'videos/home.html', {'videos': videos})


@login_required
def upload_video(request):
	if request.method == 'POST':
		video_obj = request.FILES.get('file', '')
		lang = request.POST.get('language', '')
		audio_file = extract_audio_from_video(video_obj)
		if audio_file is not None:
			del video_obj
			file_url = upload_to_gcs(audio_file, 'flagship-videos')
			speech_txt = process_speech_to_txt(file_url, lang)



