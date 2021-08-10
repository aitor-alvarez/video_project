from django.shortcuts import render, redirect
from utils.utils import *
from django.http import JsonResponse
from .models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import os
import uuid
from botocore.exceptions import ClientError
from django.contrib.auth.mixins import LoginRequiredMixin
from video.forms import *


@login_required
def showcase_videos(request):
	videos = Video.objects.filter(is_showcase=True)
	videos=[]
	for v in videos:
		video_url = get_s3_url('flagship-videos', 'videos/' + str(v.pid)+'.mp4')
		try:
			transcript_url = get_s3_url('flagship-videos', 'transcript/' + str(v.pid)+'.vtt')
		except:
			transcript_url=''
		try:
			translation_url = get_s3_url('flagship-videos', 'translations/' + str(v.pid)+'.vtt')
		except:
			translation_url =''
		videos.append((video_url, transcript_url, translation_url, v.language))

	return render(request, 'video/home.html', {'urls':  videos})


class VideoView(LoginRequiredMixin, CreateView):
		model = Video
		template_name = 'video/video_form.html'
		success_url = '/'
		fields = ['file', 'type', 'event']

		def get_initial(self, *args, **kwargs):
			profile = Profile.objects.filter(user=self.request.user)
			profile = list(profile.values_list('id', flat=True))
			programs = Program.objects.filter(students__in=profile)
			programs = list(programs.values_list('id', flat=True))
			events = Event.objects.filter(program__in=programs)
			if events:
				initial = super(VideoView, self).get_initial(**kwargs)
				initial['events'] = events
				return initial
			else:
				HttpResponseRedirect('/')


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


def generate_video(request, video_id):
	video = Video.objects.get(id=video_id)
	if request.user == video.owner.user:
		if video.is_final == False:
			return render(request, 'video/generate_video.html', {'video': video})
		else:
			error ="This video has been marked as final. You cannot regenerate transcripts or modify it."
			return render(request, 'video/generate_video.html', {'error': error})
	else:
		error = "You are not authorized to access this video"
		return render(request, 'video/generate_video.html', {'error': error})


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


def extract_audio_and_transcript(request):
	if request.is_ajax():
		video_file = request.POST.get('video_file', None)
		language = request.POST.get('language', None)
		access_code = request.POST.get('access_code', None)
		audio_file = extract_audio_from_video(video_file.split('/')[-1])
		if audio_file is not None:
			file_url, blob = upload_to_gcs(audio_file, 'flagship-videos')
			speech_txt_response = process_speech_to_txt(file_url, language)
			if speech_txt_response:
				vtt_file = generate_vtt_caption(speech_txt_response, language)
				if vtt_file is not None:
					vtt_filename = access_code+'.vtt'
					vtt_file.save(vtt_filename)
					s3_upload_file_to_bucket('tmp/transcript/'+ vtt_filename, 'videos-techcenter', 'transcripts/' + vtt_filename,
					                         {'ContentType': 'text/vtt', 'pid': access_code,
					                          'access_code': access_code, 'language': language})
					os.remove(video_file)
					os.remove(audio_file)
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
			response=audio_file
		return JsonResponse(response)


def show_video(request, video_id):
	video = Video.objects.get(id=video_id)
	video_url = get_s3_url('flagship-videos', 'videos/' + str(video.pid)+'.mp4')
	try:
		transcript_url = get_s3_url('flagship-videos', 'transcripts/' + str(video.pid)+'.vtt')
	except:
		transcript_url=None
	try:
		translation_url = get_s3_url('flagship-videos', 'translations/' + str(video.pid)+'.mp4')
	except:
		translation_url=None

	return render(request, 'video/video.html', {'video_url': video_url, 'transcript_url':transcript_url, 'translation_url'
	                                            :translation_url, 'video_object': video})
