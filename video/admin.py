from django.contrib import admin
from .models import *
from django.contrib import admin

#make admin profile searchable
class ProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = Profile
        exclude = []
    search_fields = ['first_name', 'last_name', 'email']


class VideoAdmin(admin.ModelAdmin):
    class Meta:
        model = Video
        exclude = []
    search_fields = ['title', 'pid']


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Program)
admin.site.register(Event)
admin.site.register(Language)
admin.site.register(Institution)
admin.site.register(Location)
admin.site.register(Country)

