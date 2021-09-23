from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Now
from django.dispatch import receiver
from django.db.models.signals import post_save
import datetime
from django.conf import settings

video_types = (
	('I', 'Interview'),
	('P', 'Presentation'),
	('Q', 'Presentation and Q&A'),
)

phases = (
	('F', 'Final'),
	('M', 'Mid-Program'),
)

user_choices = (
	('A', 'Admin'),
	('B', 'Staff'),
	('C', 'Student'),
)

program_choices = (
	('A', 'Academic'),
	('Y', 'Year'),
	('S', 'Summer'),
)

path2 = getattr(settings, "PATH", None)

class Profile(models.Model):
	first_name = models.CharField(max_length=255, verbose_name="First Name")
	last_name = models.CharField(max_length=255, verbose_name="Last Name")
	email = models.EmailField(blank=True)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	type = models.CharField(max_length=1, choices=user_choices, blank=True, default='C')
	language = models.ForeignKey('Language', blank=True,  null=True, on_delete=models.CASCADE)
	institution = models.ForeignKey('Institution', blank=True, null=True, on_delete=models.CASCADE)

	def __str__(self):
		return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)


class Video(models.Model):
	title = models.CharField(max_length=255, blank=True)
	file = models.FileField( upload_to='./uploads/video/',blank=True, null=True)
	description = models.TextField(blank=True)
	language = models.CharField(max_length=255, blank=True)
	url = models.URLField(blank=True)
	pid = models.CharField(max_length=255, blank=True)
	metadata = models.TextField(blank=True)
	access_code = models.CharField(max_length=255, blank=True)
	type = models.CharField(max_length=1, choices=video_types)
	is_showcase = models.BooleanField(default=0)
	is_public = models.BooleanField(default=0)
	is_internal = models.BooleanField(default=0)
	owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
	event = models.ForeignKey('Event', on_delete=models.CASCADE)
	duration = models.DurationField(null=True, blank=True)
	transcript_created = models.BooleanField(default=0)
	transcript_completed = models.BooleanField(default=0)
	is_final = models.BooleanField(default=0)
	translation_created = models.BooleanField(default=0)
	thumb_created = models.BooleanField(default=0)
	created = models.DateTimeField(default=datetime.datetime.now())

	def __str__(self):
		return self.title


class Program(models.Model):
	name = models.CharField(max_length=255)
	start = models.DateField()
	end = models.DateField()
	language = models.ForeignKey('Language', on_delete=models.CASCADE)
	program_years = models.CharField(max_length=1, choices=program_choices)
	students = models.ManyToManyField('Profile', blank=True)

	def get_events(self):
		events = Event.objects.filter(program=self)
		return events

	def __str__(self):
		return self.name


class Event(models.Model):
	program = models.ForeignKey('Program', on_delete=models.CASCADE)
	start = models.DateField()
	end = models.DateField()
	phase = models.CharField(max_length=1, choices=phases)
	city = models.ForeignKey('Location', on_delete=models.CASCADE)
	country = models.ForeignKey('Country', on_delete=models.CASCADE)

	def __str__(self):
		return self.program.name+' ('+self.get_phase_display()+')'


class Location(models.Model):
	name = models.CharField(max_length=255, blank=False)

	def __str__(self):
		return self.name


class Country(models.Model):
	name = models.CharField(max_length=255, blank=False)

	class Meta:
		verbose_name_plural = "Countries"

	def __str__(self):
		return self.name


class Language(models.Model):
	language = models.CharField(max_length=255)
	language_code = models.CharField(max_length=155)

	def __str__(self):
		return self.language


class Institution(models.Model):
	name = models.CharField(max_length=155, blank=False)

	def __str__(self):
		return self.name
