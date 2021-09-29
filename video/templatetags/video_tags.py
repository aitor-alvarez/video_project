from django import template
from video.models import Profile, Program


register = template.Library()

@register.filter(name='get_profile_type')
def get_profile_type(user):
	profile = Profile.objects.get(user=user)
	return profile.type

@register.filter(name='is_user_in_program')
def is_user_in_program(user):
	profile = Profile.objects.get(user=user)
	if Program.objects.filter(students__in=[user]).exists():
		return True
	else:
		return False