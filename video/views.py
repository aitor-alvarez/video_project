from django.shortcuts import render, redirect
from utils.utils import *
from django.http import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import os
import uuid
from botocore.exceptions import ClientError
from django.contrib.auth.mixins import LoginRequiredMixin
from video.forms import *
import webvtt
import json
import random
import boto3
import botocore



def home(request):
	videos_ids = Video.objects.filter(is_showcase=True).values_list('id', flat=True)
	videos_showcase_ids = random.sample(list(videos_ids), min(len(videos_ids), 3))
	videos_showcase = Video.objects.filter(id__in=videos_showcase_ids)
	return render(request, 'video/home.html', {'videos':  videos_showcase})


def showcase_videos(request, video_id=None):
	s3 = boto3.resource('s3')
	videos = Video.objects.filter(is_showcase=True)
	if video_id is None:
		video = videos[0]
	else:
		video = Video.objects.get(id=video_id)

	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid)+'.mp4')
	transcript_url = get_s3_url('videos-techcenter', 'transcripts/' + str(video.pid)+'.vtt')
	try:
		s3.Object('videos-techcenter', 'translations/' + str(video.pid)+'.vtt').load()
		translation_url = get_s3_url('videos-techcenter', 'translations/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			translation_url = None

	try:
		s3.Object('videos-techcenter', 'annotations/cultural/' + str(video.pid)+'.vtt').load()
		description_cultural = get_s3_url('videos-techcenter', 'annotations/cultural/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			description_cultural = None

	try:
		s3.Object('videos-techcenter',  'annotations/professional/' + str(video.pid) + '.vtt').load()
		description_professional = get_s3_url('videos-techcenter', 'annotations/professional/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			description_professional = None

	try:
		s3.Object('videos-techcenter',  'annotations/linguistic/' + str(video.pid) + '.vtt').load()
		description_linguistic = get_s3_url('videos-techcenter', 'annotations/linguistic/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			description_linguistic = None

	return render(request, 'video/showcase.html', {'videos':videos,'video_url': video_url, 'transcript_url':transcript_url,
	                                               'translation_url': translation_url, 'description_cultural_url': description_cultural,
	                                              'description_professional_url': description_professional,
	                                               'description_linguistic_url': description_linguistic,
	                                               'video_object': video })



@login_required
def my_videos(request):
	videos = Video.objects.filter(owner__user=request.user)
	return render(request, 'video/my_videos.html', {'my_videos':  videos})


class VideoView(LoginRequiredMixin, CreateView):
		model = Video
		template_name = 'video/video_form.html'
		success_url = '/'
		fields = ['is_public', 'is_internal', 'file', 'type', 'event']

		def get_initial(self, *args, **kwargs):
			profile = Profile.objects.filter(user=self.request.user)
			profile = list(profile.values_list('id', flat=True))
			programs = Program.objects.filter(students__in=profile)
			programs = list(programs.values_list('id', flat=True))
			events = Event.objects.filter(program__in=programs)
			initial = super(VideoView, self).get_initial(**kwargs)
			initial['events'] = events
			return initial


		def form_valid(self, form):
			video_form = form.save(commit=False)
			pid = uuid.uuid4().hex
			profile = Profile.objects.get(user=self.request.user)
			program = Program.objects.get(students__in=[profile])
			language = program.language.language_code
			video_form.access_code = pid
			video_form.owner = profile
			video_form.language = language
			video_form.pid = pid
			video_form.title = profile.first_name+' '+profile.last_name
			video_form.save()
			return redirect('generate_video', video_id=video_form.id)


class ProgramView(LoginRequiredMixin, CreateView):
	model = Program
	template_name = 'video/program_form.html'
	fields = ('name', 'start', 'end', 'language', 'program_years')
	success_url = '/'

	def get_initial(self, *args, **kwargs):
		profile = Profile.objects.get(user= self.request.user)
		if profile.type == 'A' or 'B':
			initial = super(ProgramView, self).get_initial(**kwargs)
			return initial
		else:
			HttpResponseRedirect('/')


class UserView(LoginRequiredMixin, CreateView):
	model = Profile
	template_name = 'video/user_form.html'
	fields = ('first_name', 'last_name', 'email', 'type', 'institution')
	success_url = '/'

	def get_initial(self, *args, **kwargs):
		profile = Profile.objects.get(user= self.request.user)
		if profile.type == 'A' or 'B':
			initial = super(UserView, self).get_initial(**kwargs)
			return initial
		else:
			HttpResponseRedirect('/')

	def form_valid(self, form):
		form.save(commit=False)
		user = User.objects.create(username=form.cleaned_data['email'], email=form.cleaned_data['email'])
		profile = Profile.objects.get(id=user.id)
		profile.user = user
		profile.email = form.cleaned_data['email']
		profile.first_name = form.cleaned_data['first_name']
		profile.last_name = form.cleaned_data['last_name']
		profile.type = form.cleaned_data['type']
		profile.save()
		return redirect('/')


@login_required
def get_users(request):
	profiles = Profile.objects.filter(user__is_staff=False)
	return render(request, 'video/users.html', {'profiles':profiles})


class EventView(LoginRequiredMixin, CreateView):
	model = Event
	template_name = 'video/event_form.html'
	form_class = EventForm

	def get_initial(self, *args, **kwargs):
		profile = Profile.objects.get(user= self.request.user)
		if profile.type == 'A' or 'B':
			initial = super(EventView, self).get_initial(**kwargs)
			initial['program'] = self.kwargs['program_id']
			return initial
		else:
			HttpResponseRedirect('/')

	def form_valid(self, form):
		form.save(commit=False)
		program_id = self.kwargs['program_id']
		form.save()
		return redirect('program_detail', program_id=program_id)


@login_required
def list_programs(request):
	profile = Profile.objects.get(user=request.user)
	if profile.type == 'A' or 'B':
		programs = Program.objects.all()
		return render(request, 'video/programs.html', {'programs': programs})
	else:
		HttpResponseRedirect('/')


@login_required
def search_user(request):
	if request.is_ajax():
		email = request.POST.get('email', None)
		program_id = request.POST.get('program_id', None)
		try:
			profile = Profile.objects.get(user__email =email)
			if not Program.objects.filter(id=program_id, students__in=[profile]).exists():
				response = {
					'first_name': profile.first_name, 'last_name': profile.last_name, 'email': email, 'profile_id': profile.id }
				return JsonResponse(response)
			else:
				response = {'error': 'There is a student with this email that is currently enrolled.'}
				return JsonResponse(response)
		except:
			response ={'error': 'There is no user with this email'}
			return JsonResponse(response)


@login_required
def enroll_user(request):
	if request.is_ajax():
		profile_id = request.POST.get('profile_id', None)
		program_id = request.POST.get('program_id', None)
		try:
			profile = Profile.objects.get(id=profile_id)
			program = Program.objects.get(id=program_id)
			program.students.add(profile)
			response = {
				'msg':'User added as student.' }
			return JsonResponse(response)
		except:
			response ={'error': 'Student could not be enrolled'}
			return JsonResponse(response)


@login_required
def program_detail(request, program_id):
	profile = Profile.objects.get(user=request.user)
	if profile.type == 'A' or 'B':
		program = Program.objects.get(id=program_id)
		return render(request, 'video/program_detail.html', {'program': program, 'profile': profile})
	else:
		HttpResponseRedirect('/')


@login_required
def generate_video(request, video_id):
	video = Video.objects.get(id=video_id)
	if video.is_final or video.transcript_created:
		return HttpResponseRedirect('/my-videos/')
	else:
		if request.user == video.owner.user:
			if video.is_final == False:
				return render(request, 'video/generate_video.html', {'video': video})
			else:
				error ="This video has been marked as final. You cannot regenerate transcripts or modify it."
				return render(request, 'video/generate_video.html', {'error': error})
		else:
			error = "You are not authorized to access this video"
			return render(request, 'video/generate_video.html', {'error': error})


@login_required
def upload_video_s3(request):
	if request.is_ajax():
		id = request.POST.get('id', None)
		video = Video.objects.get(id=id)
		try:
			s3_upload_file_to_bucket(str(video.file), 'videos-techcenter', 'videos/' + str(video.access_code) + '.mp4',
		                         {'ContentType':'video/mp4','pid': str(video.pid), 'access_code': str(video.access_code), 'language': video.language})
			response = {
				'msg': 'The video is ready for audio segmentation.'}
		except ClientError as e:
			response = {
				'msg': e}
		return JsonResponse(response)


@login_required
def extract_audio_and_transcript(request):
	if request.is_ajax():
		video_id = request.POST.get('video_id', None)
		video_file = request.POST.get('video_file', None)
		language = request.POST.get('language', None)
		access_code = request.POST.get('access_code', None)
		audio_file = extract_audio_from_video(video_file.split('/')[-1])
		video = Video.objects.get(id=video_id)
		if audio_file is not None:
			file_url, blob = upload_to_gcs(audio_file, 'flagship-videos')
			speech_txt_response = process_speech_to_txt(file_url, language)
			if speech_txt_response:
				vtt_file = generate_vtt_caption(speech_txt_response, language)
				if vtt_file is not None:
					vtt_filename = access_code+'.vtt'
					vtt_file.save('tmp/transcript/'+vtt_filename)
					s3_upload_file_to_bucket('tmp/transcript/'+ vtt_filename, 'videos-techcenter', 'transcripts/' + vtt_filename,
					                         {'ContentType': 'text/vtt', 'pid': access_code,
					                          'access_code': access_code, 'language': language})
					video.transcript_created = True
					video.save()
					try:
						thumb_file = 'tmp/thumbs/'+access_code+'.jpg'
						thumb = generate_thumb(video_file, thumb_file, 480)
						s3_upload_file_to_bucket(thumb_file, 'videos-techcenter',
						                         'thumbs/' +access_code+'.jpg',
						                         {'ContentType': 'image/jpeg', 'pid': access_code,
						                          'access_code': access_code, 'language': language})
						video.thumb_created = True
						video.save()
					except:
						print("no thumb")
					os.remove(video_file)
					os.remove(audio_file)
					os.remove(thumb_file)
					blob.delete()
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
			response = {
					'msg': 'The video file has some errors and audio could not be extracted.'}
		return JsonResponse(response)



def show_video(request, video_id):
	video = Video.objects.get(id=video_id)
	if video.is_public or video.owner.user == request.user:
		video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid)+'.mp4')
		if video.transcript_created == True:
				transcript_url = get_s3_url('videos-techcenter', 'transcripts/' + str(video.pid)+'.vtt')

		else:
			transcript_url=None
		if video.is_final==True:
			translation_url = get_s3_url('videos-techcenter', 'translations/' + str(video.pid)+'.vtt')
		else:
			translation_url=None

		return render(request, 'video/video.html', {'video_url': video_url, 'transcript_url':transcript_url, 'translation_url'
		                                            :translation_url, 'video_object': video})
	else:
		return render(request, 'video/video.html', {'error': True})


def edit_transcript(request, video_id):
	video = Video.objects.get(id=video_id)
	transcript_file = 'tmp/transcript/'+video.access_code+'.vtt'
	transcript = get_s3_url('videos-techcenter', 'transcripts/'+video.access_code+'.vtt')
	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid) + '.mp4')
	output = []
	for caption in webvtt.read(transcript_file):
		vtt_file = {}
		vtt_file['start'] = caption.start
		vtt_file['end'] = caption.end
		vtt_file['text'] = caption.text
		output.append(vtt_file)

	return render(request, 'video/video_edit.html', {'video': video, 'output':output,
	                                                 'video_url': video_url})


def save_vtt_s3(request):
	if request.is_ajax():
		data = request.POST.getlist('requestData[]', [])
		filename = request.POST.get('file')
		lang = request.POST.get('lang')
		video_id = request.POST.get('video_id')
		final = int(request.POST.get('final'))
		final_video = int(request.POST.get('final_video'))
		print(final)
		if final == 1:
			vid = Video.objects.get(id=video_id)
			vid.transcript_completed = final
			vid.save()
		elif final_video == 1:
			vid = Video.objects.get(id=video_id)
			vid.is_final = final_video
			vid.save()

		data = [json.loads(d) for d in data]
		vtt = WebVTT()
		for d in data:
			caption = Caption(
				d['start'],
				d['end'],
				d['text']
			)
			vtt.captions.append(caption)
		try:
			vtt.save('tmp/transcript/'+filename+'.vtt')
			s3_upload_file_to_bucket('tmp/transcript/' + filename+'.vtt', 'videos-techcenter', 'transcripts/' + filename+'.vtt',
			                         {'ContentType': 'text/vtt', 'pid': filename,
			                          'access_code': filename, 'language':lang})
			response = {
				'msg': 'The file has been saved correctly'}
		except:
			response = {
				'msg': 'The file was not saved correctly'}
		return JsonResponse(response)


def update_consent(request, video_id):
	context = {}
	obj = Video.objects.get(id=video_id)

	form = ConsentForm(request.POST or None, instance=obj)

	if form.is_valid():
		form.save()
		return HttpResponseRedirect("/my-videos")
	context["form"] = form

	return render(request, "video/consent_update.html", context)
