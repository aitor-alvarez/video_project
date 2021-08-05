"""video_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from video.views import *

urlpatterns = [
		path('', showcase_videos),
    path('admin/', admin.site.urls),
		path('new/program/', ProgramView.as_view()),
		path('new/event/<int:program_id>/', EventView.as_view()),
		path('upload/', VideoView.as_view()),
		path('ajax/upload_video/', upload_video_s3),
		path('ajax/transcribe/', extract_audio_and_transcript),
		path('programs/', list_programs),
		path('ajax/search_user/', search_user),
		path('ajax/enroll_user/', enroll_user),
		path('program/<int:program_id>/', program_detail, name='program_detail'),
		path('generate/<int:video_id>/', generate_video, name='generate_video')
]
