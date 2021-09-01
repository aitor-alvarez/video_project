from django.contrib import admin
from django.urls import path, include, re_path
from video.views import *
from django.views.generic import TemplateView
from django.conf.urls.static import static

urlpatterns = [
		path('', home),
		path('about/', TemplateView.as_view(template_name='video/about.html')),
		path('showcase/', showcase_videos),
		path('showcase/<int:video_id>', showcase_videos),
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
		path('edit-transcript/<int:video_id>/', edit_transcript),
		path('edit-transcript/<int:video_id>/<str:lang>', edit_transcript),
		path('programs/', list_programs),
		path('ajax/search_user/', search_user),
		path('ajax/enroll_user/', enroll_user),
		path('ajax/save_transcript/', save_transcript_s3),
		path('ajax/save_translation/', save_translation_s3),
		path('ajax/translate_transcript/', translate_vtt),
		path('program/<int:program_id>/', program_detail, name='program_detail'),
		path('generate/<int:video_id>/', generate_video, name='generate_video'),
		path('update_consent/<int:video_id>/', update_consent, name='update_consent')
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
