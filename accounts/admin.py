from django.contrib import admin
from accounts.models import User, UserProfile
from django.contrib.auth.admin import UserAdmin

class UserPrAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution')

admin.site.register(UserProfile, UserPrAdmin)
admin.site.register(User, UserAdmin)
