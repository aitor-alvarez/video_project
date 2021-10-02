from django.forms import ModelForm
from .models import *
from django import forms
from .models import video_types, phases

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
			if name == 'start' or name == 'end':
				self.fields[name].widget.attrs.update({
					'class': 'form-control datepicker',
				})
			else:
				self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Event
		fields = '__all__'


class UserForm(ModelForm):
	email = forms.EmailField(required=True)
	def __init__(self, *args, **kwargs):
		super(UserForm, self).__init__(*args, **kwargs)
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})

	class Meta:
		model = Profile
		fields = ('first_name', 'last_name', 'email', 'type',)


class FilterResultsForm(forms.Form):
	years =(('', '--------'), ('2017', 2017), ('2018', 2018), ('2019',2019), ('2020', 2020), ('2021', 2021), ('2022', 2022), ('2023', 2023), ('2024',2024))
	program = forms.ModelChoiceField(
				widget=forms.Select,
        queryset= Language.objects.all(), required=False)

	institution = forms.ModelChoiceField(
				widget=forms.Select,
        queryset= Institution.objects.all(), required=False
	)

	year = forms.ChoiceField(
				widget=forms.SelectMultiple,
        choices= years, required=False
	)

	type = forms.ChoiceField(
				widget=forms.Select,
        choices= (('', '-------'),)+video_types, required=False
	)

	location = forms.ModelChoiceField(
				widget=forms.Select,
        queryset= Location.objects.all(), required=False
	)

	phase = forms.ChoiceField(
				widget=forms.Select,
        choices= (('', '-------'),)+phases, required=False
	                          )

	def __init__(self, *args, **kwargs):
		super(FilterResultsForm, self).__init__(*args, **kwargs)
		for name in self.fields.keys():
			self.fields[name].widget.attrs.update({
				'class': 'form-control',
			})