from django.forms import ModelForm
from .models import *
from django import forms


class VideoForm(ModelForm):
	title = forms.HiddenInput()
	language = forms.HiddenInput()
	owner = forms.HiddenInput()

	def __init__(self, *args, **kwargs):
		super(VideoForm, self).__init__(*args, **kwargs)
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Video
		exclude =('created', 'metadata', 'url', 'pid', 'access_code', 'duration', 'is_showcase', 'title', 'owner')



