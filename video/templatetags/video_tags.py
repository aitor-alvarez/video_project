from django import template
from video.models import Profile

register = template.Library()

@register.filter(name='get_profile_type')
def get_profile_type(user):
	profile = Profile.objects.get(user=user)
	return profile.type