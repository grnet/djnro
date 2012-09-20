from django.contrib import admin
from accounts.models import *
from django.contrib.auth.models import User
from django.conf import settings
from edumanage.models import *

class UserPrAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution')

admin.site.register(UserProfile, UserPrAdmin)