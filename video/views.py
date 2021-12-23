from django.shortcuts import render, redirect
from utils.utils import *
from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import os
from botocore.exceptions import ClientError
from django.contrib.auth.mixins import LoginRequiredMixin
from video.forms import *
import webvtt
import json
import random
import boto3
import botocore
from io import StringIO
import uuid
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime
from functools import reduce
import operator
from django.db.models import Q
from django.core.mail import send_mail
import sys
import mimetypes


def home(request):
	videos_ids = Video.objects.filter(is_showcase=True).values_list('id', flat=True)
	videos_showcase_ids = random.sample(list(videos_ids), min(len(videos_ids), 3))
	videos_showcase = Video.objects.filter(id__in=videos_showcase_ids)
	return render(request, 'video/home.html', {'videos':  videos_showcase})


@login_required
def manage_programs(request):
	profile = Profile.objects.get(user=request.user)
	programs = Program.objects.all()
	events = Event.objects.all()
	users = Profile.objects.all()
	if profile.type == 'A':
		programs = Program.objects.all()
		events = Event.objects.all()
		users = Profile.objects.filter(type__in=['A', 'B'])
	elif profile.type == 'B':
		programs = Program.objects.filter(id=profile.program_id)
		events = Event.objects.filter(program__in=programs)
	return render(request, 'video/manage.html', {'programs': programs, 'events': events, 'users': users})


def showcase_videos(request, video_id=None):
	s3 = boto3.resource('s3')
	videos = Video.objects.filter(is_showcase=True)
	if video_id is None:
		video = videos[0]
	else:
		video = Video.objects.get(id=video_id)

	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid)+'.mp4')
	try:
		s3.Object('videos-techcenter', 'transcripts/' + str(video.pid) + '.vtt').load()
		transcript_url = get_s3_url('videos-techcenter', 'transcripts/' + str(video.pid)+'.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			transcript_url = None

	try:
		s3.Object('videos-techcenter', 'translations/' + str(video.pid)+'.vtt').load()
		translation_url = get_s3_url('videos-techcenter', 'translations/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			translation_url = None

	try:
		s3.Object('videos-techcenter', 'descriptions/' + str(video.pid)+'.vtt').load()
		descriptions = get_s3_url('videos-techcenter', 'descriptions/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			descriptions = None

	return render(request, 'video/showcase.html', {'videos':videos,'video_url': video_url, 'transcript_url':transcript_url,
	                                               'translation_url': translation_url, 'descriptions_url': descriptions,
	                                               'video_object': video })


@login_required
def my_videos(request):
	videos = Video.objects.filter(owner=request.user)
	return render(request, 'video/my_videos.html', {'my_videos':  videos})


@login_required
def archive_view(request):
	form = FilterResultsForm()
	profile = Profile.objects.get(user=request.user)
	if profile.type == 'A':
		videos = Video.objects.all()
	elif profile.type == 'B':
		videos = Video.objects.filter(is_internal=True)
	elif profile.type == 'C':
		return HttpResponse("<h3>You are not authorized to access this page.</h3>")

	videos = [(v, get_s3_url('videos-techcenter', 'thumbs/' + str(v.pid) + '.jpg')) for v in videos]
	page = request.GET.get('page', 1)
	paginator = Paginator(videos, 20)
	try:
		video_page = paginator.page(page)
	except PageNotAnInteger:
		video_page = paginator.page(1)
	except EmptyPage:
		video_page = paginator.page(paginator.num_pages)
	return render(request, 'video/archive.html', {'videos':video_page, 'form': form})


def filtered_archive_view(request):
	form = FilterResultsForm()
	profile = Profile.objects.get(user=request.user)
	if request.method =='POST':
		filters = {}
		program = request.POST.getlist('program')
		institution = request.POST.get('institution')
		year = request.POST.getlist('year')
		type = request.POST.get('type')
		location = request.POST.get('location')
		phase = request.POST.get('phase')
		if program !=[]:
			filters['event__program__language_id__in'] = [int(p) for p in program]
		if institution != '':
			filters['owner__institution_id'] = institution
		if type != '' :
			filters['type'] = type
		if year !=[]:
			query = reduce(operator.or_, (Q(event__program__start__gte=datetime.date(year=int(y), month=1, day=1 )) & Q(event__program__end__lte=datetime.date(year=int(y), month=12, day=31 )) for y in year) )
		else:
			query = Q(event__program__start__gte=datetime.date(year=int(2018), month=1, day=1 )) & Q(event__program__end__lte=datetime.date(year=int(2040), month=12, day=31 ))

		if location != '':
			filters['event__city_id'] = location
		if phase != '':
			filters['event__phase'] = phase

		if profile.type == 'A':
			videos = Video.objects.filter(query).filter(**filters)
		elif profile.type == 'B':
			videos = Video.objects.filter(query).filter(**filters, is_internal=True)
		elif profile.type == 'C':
			return HttpResponse("<h3>You are not authorized to access this page.</h3>")
	elif request.method == 'GET':
		profile = Profile.objects.get(user=request.user)
		if profile.type == 'A':
			videos = Video.objects.all()
		elif profile.type == 'B':
			videos = Video.objects.filter(is_internal=True)
		elif profile.type == 'C':
			return HttpResponse("<h3>You are not authorized to access this page.</h3>")

	videos = [(v, get_s3_url('videos-techcenter', 'thumbs/' + str(v.pid) + '.jpg')) for v in videos]
	page = request.GET.get('page', 1)
	paginator = Paginator(videos, 20)
	try:
		video_page = paginator.page(page)
	except PageNotAnInteger:
		video_page = paginator.page(1)
	except EmptyPage:
		video_page = paginator.page(paginator.num_pages)
	return render(request, 'video/archive.html', {'videos': video_page, 'form': form})


class VideoView(LoginRequiredMixin, CreateView):
		model = Video
		template_name = 'video/video_form.html'
		form_class = UploadVideo


		def form_valid(self, form):
			video_form = form.save(commit=False)
			pid = uuid.uuid4().hex
			profile = Profile.objects.get(user=self.request.user)
			program = video_form.event.program
			language = program.language.language_code
			video_form.access_code = pid
			video_form.owner = self.request.user
			video_form.language = language
			video_form.pid = pid
			video_form.title = profile.first_name+' '+profile.last_name
			video_form.save()
			mime = mimetypes.guess_type(str(video_form.file))
			if 'video' in mime[0]:
				return redirect('generate_video', video_id=video_form.id)
			else:
				video_form.delete()
				os.remove(str(video_form.file))
				return render(self.request, 'video/video_form.html', {'error': 'The mime type of the file is not video/mp4. Please upload the correct file type. '})

		def get_initial(self, *args, **kwargs):
			initial = super(VideoView, self).get_initial(*args, **kwargs)
			programs = Program.objects.filter(students__in=[self.request.user]).values_list('id', flat=True)
			events = Event.objects.filter(program__in=programs)
			initial['event'] = events
			return initial


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
	form_class = UserForm
	success_url = '/manage'

	def get_initial(self, *args, **kwargs):
		profile = Profile.objects.get(user= self.request.user)
		if profile.type == 'A' or 'B':
			initial = super(UserView, self).get_initial(**kwargs)
			return initial
		else:
			HttpResponseRedirect('/')

	def form_valid(self, form):
		form.save(commit=False)
		password = uuid.uuid1()
		password = str(password.hex[0:8])
		user = User.objects.create(username=form.cleaned_data['email'], email=form.cleaned_data['email'],
		                           first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'])
		user.set_password(password)
		profile = Profile.objects.get(user=user)
		profile.user = user
		profile.email = form.cleaned_data['email']
		profile.first_name = form.cleaned_data['first_name']
		profile.last_name = form.cleaned_data['last_name']
		profile.type = form.cleaned_data['type']
		profile.save()
		try:
			send_mail(
				'Flagship Video Project: new account',
				'A request has been received to create an account with your email. Your username is your email address.\n' + 'Please, create your password using the following form: https://' + self.request.get_host() + '/accounts/password_reset/',
				'Flagship Video Project', [form.cleaned_data['email']])

		except:
			e = sys.exc_info()
			return redirect('/error_email')
		return redirect('/manage')


class CreateStudentView(LoginRequiredMixin, CreateView):
	model = Profile
	template_name = 'video/student_form.html'
	form_class = UserForm
	success_url = '/manage'

	def get_initial(self, *args, **kwargs):
		profile = Profile.objects.get(user= self.request.user)
		if profile.type == 'A' or 'B':
			initial = super(CreateStudentView, self).get_initial(**kwargs)
			return initial
		else:
			HttpResponseRedirect('/')


	def form_valid(self, form):
		if User.objects.filter(username=form.cleaned_data['email']).exists():
			return redirect('/error_user')
		else:
			program = Program.objects.get(id=self.kwargs['program_id'])
			form.save(commit=False)
			password = uuid.uuid1()
			password = str(password.hex[0:8])
			user = User.objects.create(username=form.cleaned_data['email'], email=form.cleaned_data['email'], first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'])
			user.set_password(password)
			program.students.add(user)
			profile = Profile.objects.get(user=user)
			profile.user = user
			profile.email = form.cleaned_data['email']
			profile.first_name = form.cleaned_data['first_name']
			profile.last_name = form.cleaned_data['last_name']
			profile.type = form.cleaned_data['type']
			profile.language = program.language
			profile.institution = form.cleaned_data['institution']
			profile.program = program
			profile.save()
			try:
				send_mail(
					'Flagship Video Project: new account',
					'A request has been received to create an account with your email. Your username is your email address.\n' + 'Please, create your password using the following form: https://' + self.request.get_host() + '/accounts/password_reset/',
					'Flagship Video Project', [form.cleaned_data['email']])

			except:
				e = sys.exc_info()
				print(e)
				return redirect('/error_email')
			return redirect('/manage')


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
			if not Program.objects.filter(id=program_id, students__in=[profile.user]).exists():
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
			program.students.add(profile.user)
			program.save()
			response = {
				'msg':'User added as student.' }
			return JsonResponse(response)
		except:
			response ={'error': 'Student could not be enrolled'}
			return JsonResponse(response)


@login_required
def program_detail(request, program_id):
	profile = Profile.objects.get(user=request.user)
	if profile.type == 'A' or profile.type == 'B':
		program = Program.objects.get(id=program_id)
		return render(request, 'video/program_detail.html', {'program': program, 'profile': profile})
	else:
		HttpResponseRedirect('/')


@login_required
def generate_video(request, video_id):
	video = Video.objects.get(id=video_id)
	profile = Profile.objects.get(user=request.user)
	if video.is_final or video.transcript_created:
		return HttpResponseRedirect('/my-videos/')
	else:
		if request.user == video.owner:
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
	path = getattr(settings, "PATH", None)
	if request.is_ajax():
		id = request.POST.get('id', None)
		video = Video.objects.get(id=id)
		try:
			s3_upload_file_to_bucket(path+str(video.file), 'videos-techcenter', 'videos/' + str(video.access_code) + '.mp4',
		                         {'ContentType':'video/mp4','pid': str(video.pid), 'access_code': str(video.access_code), 'language': video.language})
			response = {
				'msg': 'The video is ready for audio segmentation.'}
		except ClientError as e:
			response = {
				'msg': e}
		return JsonResponse(response)


@login_required
def extract_audio_and_transcript(request):
	path = getattr(settings, "PATH", None)
	if request.is_ajax():
		video_id = request.POST.get('video_id', None)
		video_file = request.POST.get('video_file', None)
		language = request.POST.get('language', None)
		access_code = request.POST.get('access_code', None)
		audio_file, duration = extract_audio_from_video(video_file.split('/')[-1])
		audio_file_name = audio_file.split('/')[-1]
		video = Video.objects.get(id=video_id)
		video.duration = duration
		video.save()
		if audio_file is not None:
			file_url, blob = upload_to_gcs(audio_file, audio_file_name, 'flagship-videos')
			speech_txt_response = process_speech_to_txt(file_url, language)
			if speech_txt_response:
				vtt_file = generate_vtt_caption(speech_txt_response, language)
				if vtt_file is not None:
					vtt_filename = access_code+'.vtt'
					vtt_file.save(path+'uploads/transcript/'+vtt_filename)
					s3_upload_file_to_bucket(path+'uploads/transcript/'+ vtt_filename, 'videos-techcenter', 'transcripts/' + vtt_filename,
					                         {'ContentType': 'text/vtt', 'pid': access_code,
					                          'access_code': access_code, 'language': language})
					video.transcript_created = True
					video.save()
					try:
						thumb_file = path+'uploads/thumbs/'+access_code+'.jpg'
						thumb = generate_thumb(path+'uploads/video/'+access_code+'.mp4', thumb_file, 480)
						s3_upload_file_to_bucket(thumb_file, 'videos-techcenter',
						                         'thumbs/' +access_code+'.jpg',
						                         {'ContentType': 'image/jpeg', 'pid': access_code,
						                          'access_code': access_code, 'language': language})
						video.thumb_created = True
						video.save()
					except:
						print("no thumb")
					try:
						blob.delete()
						os.remove(thumb_file)
						os.remove(path + video.file)
						os.remove(path + 'uploads/audio/' + audio_file_name)
						os.remove(path + 'uploads/transcript/' + vtt_filename)
					except:
						None
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
	s3 = boto3.resource('s3')
	if video.is_public == True:
		video_url, transcript_url, translation_url, video = get_video_s3(video, s3)
		return render(request, 'video/video.html',
		              {'video_url': video_url, 'transcript_url': transcript_url, 'translation_url'
		              : translation_url, 'video_object': video})

	elif video.is_public == False:
		if request.user.is_authenticated:
			profile = Profile.objects.get(user=request.user)
			if profile.type == 'A' or video.owner == request.user:
				video_url, transcript_url, translation_url, video = get_video_s3(video, s3)
				return render(request, 'video/video.html',
				              {'video_url': video_url, 'transcript_url': transcript_url, 'translation_url': translation_url,
				               'video_object': video})
			elif  profile.type == 'B' and video.is_internal == True:
				video_url, transcript_url, translation_url, video = get_video_s3(video, s3)
				return render(request, 'video/video.html', {'video_url': video_url, 'transcript_url':transcript_url, 'translation_url':translation_url, 'video_object': video})
			else:
				return render(request, 'video/video.html', {'error': True})
		else:
			return HttpResponseRedirect('/accounts/login/')


def get_video_s3(video, s3):
	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid) + '.mp4')
	if video.transcript_created == True:
		try:
			s3.Object('videos-techcenter', 'transcripts/' + str(video.pid) + '.vtt').load()
			transcript_url = get_s3_url('videos-techcenter', 'transcripts/' + str(video.pid) + '.vtt')
		except botocore.exceptions.ClientError as e:
			if e.response['Error']['Code'] == "404":
				transcript_url = False
	else:
		transcript_url = None
	try:
		s3.Object('videos-techcenter', 'translations/' + str(video.pid) + '.vtt').load()
		translation_url = get_s3_url('videos-techcenter', 'translations/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			translation_url = False
	return video_url, transcript_url, translation_url, video


@login_required
def show_private_video(request, access_code):
	s3 = boto3.resource('s3')
	video = Video.objects.get(access_code=access_code)
	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid)+'.mp4')
	try:
		s3.Object('videos-techcenter', 'transcripts/' + str(video.pid) + '.vtt').load()
		transcript_url = get_s3_url('videos-techcenter', 'transcripts/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			transcript_url = False

	try:
		s3.Object('videos-techcenter', 'translations/' + str(video.pid) + '.vtt').load()
		translation_url = get_s3_url('videos-techcenter', 'translations/' + str(video.pid) + '.vtt')
	except botocore.exceptions.ClientError as e:
		if e.response['Error']['Code'] == "404":
			translation_url = False

	return render(request, 'video/private_video.html', {'video_url': video_url, 'transcript_url':transcript_url, 'translation_url'
		                                            :translation_url, 'video_object': video})


@login_required
def edit_transcript(request, video_id, lang=None):
	video = Video.objects.get(id=video_id)
	s3_client = boto3.client('s3')
	if lang == None:
		s3_response_object = s3_client.get_object(Bucket='videos-techcenter', Key='transcripts/' + video.pid+'.vtt')
		file_content = s3_response_object['Body'].read()
		transcript_file = webvtt.read_buffer(StringIO(file_content.decode()))
	elif lang == 'en':
		s3_response_object = s3_client.get_object(Bucket='videos-techcenter',
		                                          Key='translations/' + video.pid + '.vtt')
		file_content = s3_response_object['Body'].read()
		transcript_file = webvtt.read_buffer(StringIO(file_content.decode()))

	video_url = get_s3_url('videos-techcenter', 'videos/' + str(video.pid) + '.mp4')
	output = []
	for caption in transcript_file:
		vtt_file = {}
		vtt_file['start'] = caption.start
		vtt_file['end'] = caption.end
		vtt_file['text'] = caption.text
		output.append(vtt_file)

	return render(request, 'video/video_edit.html', {'video': video, 'output':output,
	                                                 'video_url': video_url})


@login_required
def save_transcript_s3(request):
	vtt, filename, lang = parse_vtt(request)
	path = getattr(settings, "PATH", None)
	try:
		vtt.save(path+'uploads/transcript/'+filename+'.vtt')
		s3_upload_file_to_bucket(path+'uploads/transcript/' + filename+'.vtt', 'videos-techcenter', 'transcripts/' + filename+'.vtt',
			                         {'ContentType': 'text/vtt', 'pid': filename,
			                          'access_code': filename, 'language':lang})
		os.remove('./uploads/transcript/'+filename+'.vtt')
		response = {
				'msg': 'The file has been saved correctly'}
	except botocore.exceptions.ClientError as error:
		response = {
				'msg': error}
	return JsonResponse(response)


@login_required
def save_translation_s3(request):
	vtt, filename, lang = parse_vtt(request)
	path = getattr(settings, "PATH", None)
	try:
		vtt.save(path+'uploads/translation/'+filename+'.vtt')
		s3_upload_file_to_bucket(path+'uploads/translation/' + filename+'.vtt', 'videos-techcenter', 'translations/' + filename+'.vtt',
			                         {'ContentType': 'text/vtt', 'pid': filename,
			                          'access_code': filename, 'language':lang})
		os.remove('../uploads/translation/'+filename+'.vtt')
		response = {
				'msg': 'The file has been saved correctly'}
	except:
		response = {
				'msg': 'The file was not saved correctly'}
	return JsonResponse(response)


@login_required
def parse_vtt(request):
	if request.is_ajax():
		data = request.POST.getlist('requestData[]', [])
		filename = request.POST.get('file')
		lang = request.POST.get('lang')
		video_id = request.POST.get('video_id')
		final = int(request.POST.get('final'))
		final_video = int(request.POST.get('final_video'))
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
	return vtt, filename, lang


@login_required
def update_consent(request, video_id):
	context = {}
	obj = Video.objects.get(id=video_id)

	form = ConsentForm(request.POST or None, instance=obj)

	if form.is_valid():
		form.save()
		return HttpResponseRedirect("/my-videos")
	context["form"] = form

	return render(request, "video/consent_update.html", context)


@login_required
def translate_vtt(request):
	if request.is_ajax():
		path = getattr(settings, "PATH", None)
		filename = request.POST.get('file')
		lang = request.POST.get('lang')
		video_id = request.POST.get('video_id')
		s3_client = boto3.client('s3')
		video = Video.objects.get(id=video_id)
		s3_response_object = s3_client.get_object(Bucket='videos-techcenter', Key='transcripts/' + filename)
		file_content = s3_response_object['Body'].read()
		file_content = webvtt.read_buffer(StringIO(file_content.decode()))
		translate_vtt = generate_translation(file_content, lang)
		try:
			if translate_vtt is not None:
				translate_vtt.save(path+'uploads/translation/' + filename)
				s3_upload_file_to_bucket(path+'uploads/translation/' + filename, 'videos-techcenter', 'translations/' + filename,
				                         {'ContentType': 'text/vtt', 'language': 'en'})
				video.translation_created = True
				video.save()
				os.remove(path+'uploads/translation/' + filename)
				os.remove(path+'uploads/transcript/' + filename)
				response = {
					'msg': 'The translation was processed correctly.'}
				return JsonResponse(response)

		except:
			response = {
				'msg': 'The file was not translated correctly. Please try again.'}
			return JsonResponse(response)

