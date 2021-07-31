from django.forms import ModelForm
from .models import *
from django import forms


class VideoForm(ModelForm):
	video_file = forms.FileField()
	language = forms.HiddenInput()

	def __init__(self, *args, **kwargs):
		super(VideoForm, self).__init__(*args, **kwargs)
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Video
		exclude =('created',)


