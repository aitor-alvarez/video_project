from django.contrib import admin
from django.urls import path, include
from video.views import *
from django.views.generic import TemplateView
from django.conf.urls.static import static


urlpatterns = [
		path('', home),
		path('my-videos/', my_videos),
		path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
		path('new/program/', ProgramView.as_view()),
		path('video/<int:video_id>/', show_video),
		path('manage/', TemplateView.as_view(template_name='video/manage.html')),
		path('new/user/', UserView.as_view()),
		path('new/event/<int:program_id>/', EventView.as_view()),
		path('users/', get_users),
		path('upload/', VideoView.as_view()),
		path('ajax/upload_video/', upload_video_s3),
		path('ajax/transcribe/', extract_audio_and_transcript),
		path('programs/', list_programs),
		path('ajax/search_user/', search_user),
		path('ajax/enroll_user/', enroll_user),
		path('program/<int:program_id>/', program_detail, name='program_detail'),
		path('generate/<int:video_id>/', generate_video, name='generate_video')
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
