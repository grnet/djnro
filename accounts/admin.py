from django.contrib import admin
from accounts.models import User, UserProfile
from django.contrib.auth.admin import UserAdmin

@admin.register(UserProfile)
class UserPrAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'is_social_active')

admin.site.register(User, UserAdmin)
