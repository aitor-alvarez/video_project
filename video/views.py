from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from utils.utils import *
from django.http import JsonResponse
from botocore.exceptions import ClientError
import logging
from .models import *
from django.views.generic.edit import FormView
from .forms import VideoForm
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import asyncio
import os
import uuid
from botocore.exceptions import ClientError


@login_required
def showcase_videos(request):
	videos = Video.objects.filter(is_showcase=True)
	return render(request, 'video/home.html', {'videos': videos})


class VideoView(CreateView):
		model = Video
		template_name = 'video/video_form.html'
		success_url = '/'
		fields = [ 'file', 'type', 'event']

		def form_valid(self, form):
			video_form = form.save(commit=False)
			last_id = Video.objects.latest('id')
			pid = last_id.id+1
			profile = Profile.objects.get(user=self.request.user)
			program = Program.objects.get(students__in=[profile])
			language = program.language.language_code
			video_form.access_code = uuid.uuid4().hex
			video_form.owner= profile
			video_form.language = language
			video_form.pid = pid
			video_form.title = profile.first_name+' '+profile.last_name
			video_form.save()
			return redirect('generate_video', video_id=video_form.id)


def generate_video(request, video_id):
	video = Video.objects.get(id=video_id)
	if request.user == video.owner.user:
		return render(request, 'video/generate_video.html', {'video': video})
	else:
		return HttpResponse("You are not authorized to access this video")


def upload_video_s3(request):
	if request.is_ajax():
		id = request.POST.get('id', None)
		video = Video.objects.get(id=id)
		try:
			s3_upload_file_to_bucket(str(video.file), 'videos-techcenter', 'videos/' + str(video.access_code) + '.mp4',
		                         {'ContentType':'video/mp4','pid': str(video.pid), 'access_code': str(video.access_code), 'language': video.language})
			response = {
				'msg': 'Video uploaded successfully.'}
		except ClientError as e:
			response = {
				'msg': e}
		return JsonResponse(response)


def extract_audio_and_transcript(request):
	if request.is_ajax():
		video_file = request.POST.get('video_file', None)
		language = request.POST.get('language', None)
		audio_file = extract_audio_from_video(video_file.split('/')[-1])
		if audio_file is not None:
			file_url, blob = upload_to_gcs(audio_file, 'flagship-videos')
			speech_txt_response = process_speech_to_txt(file_url, language)
			if speech_txt_response:
				vtt_path = generate_vtt_caption(speech_txt_response)
				if vtt_path is not None:
					os.remove(video_file)
					os.remove(audio_file)
					#blob.delete()
					response = {
						'msg': 'Transcript generated successfully.'}
				else:
					response = {
						'msg': 'The video file has some errors and audio could not be extracted.'}
				return JsonResponse(response)
			else:
				response = {
					'msg': 'The video file has some errors and audio could not be extracted.'}
		else:
			response=audio_file
		return JsonResponse(response)


