from django.forms import ModelForm
from .models import *
from django import forms


class ConsentForm(ModelForm):

	def __init__(self, *args, **kwargs):
		super(ConsentForm, self).__init__(*args, **kwargs)
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Video
		fields = ('is_internal', 'is_public')


class EventForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(EventForm, self).__init__(*args, **kwargs)
		self.fields['program'].disabled = True
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Event
		fields = '__all__'