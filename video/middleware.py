#Checks whether a user has approved the terms and conditions and if not redirects the user to that page.

from .models import Profile
from django.http import HttpResponseRedirect


class TermsMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response


	def __call__(self, request):
		if request.user.is_authenticated:
			profile = Profile.objects.get(user=request.user)
			if (profile.type == 'A' or profile.type == 'B') and profile.terms_of_use !=0:
				HttpResponseRedirect('/terms')
			else:
				response = self.get_response(request)
				return response

