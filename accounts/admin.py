from django.contrib import admin
from accounts.models import UserProfile


class UserPrAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution')

admin.site.register(UserProfile, UserPrAdmin)
