from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Now
from django.dispatch import receiver
from django.db.models.signals import post_save

video_types = (
	('I', 'Interview'),
	('P', 'Presentation'),
	('Q', 'Presentation and Q&A'),
)

visibility_type = (
	('I', 'Internal'),
	('P', 'Public'),
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


class Profile(models.Model):
	first_name = models.CharField(max_length=255)
	last_name = models.CharField(max_length=255)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	type = models.CharField(max_length=1, choices=user_choices, blank=True, default='C')
	institution = models.ForeignKey('Institution', on_delete=models.CASCADE)

	def __str__(self):
		return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)


class Video(models.Model):
	title = models.CharField(max_length=255)
	access_code = models.CharField(max_length=255)
	description = models.TextField()
	type = models.CharField(max_length=1, choices=video_types)
	is_showcase = models.BooleanField(default=0)
	visibility = models.CharField(max_length=1, choices=visibility_type)
	owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
	event = models.ForeignKey('Event', on_delete=models.CASCADE)
	duration = models.IntegerField()
	created = models.DateTimeField(default=Now())

	def __str__(self):
		return self.title


class Program(models.Model):
	name = models.CharField(max_length=255)
	start = models.DateField()
	end = models.DateField()
	language = models.ForeignKey('Language', on_delete=models.CASCADE)
	program_years = models.CharField(max_length=255)
	students = models.ManyToManyField(Profile)

	def __str__(self):
		return self.name


class Event(models.Model):
	program = models.ForeignKey('Program', on_delete=models.CASCADE)
	start = models.DateField()
	end = models.DateField()
	phase = models.CharField(max_length=1, choices=phases)
	city = models.CharField(max_length=155)
	country = models.CharField(max_length=155)

	def __str__(self):
		return self.program.name


class Language(models.Model):
	language = models.CharField(max_length=255)
	language_code = models.CharField(max_length=155)

	def __str__(self):
		return self.language


class Institution(models.Model):
	name = models.CharField(max_length=155, blank=False)

	def __str__(self):
		return self.name
