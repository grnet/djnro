from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from accounts.models import User, UserProfile
from django.contrib.auth.admin import UserAdmin

@admin.register(UserProfile)
class UserPrAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'is_social_active')


class HasProfileListFilter(admin.SimpleListFilter):
    title = 'has profile'
    parameter_name = 'has_profile'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(userprofile__isnull=False)
        if self.value() == 'no':
            return queryset.filter(userprofile__isnull=True)
        return queryset


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        'date_joined', 'last_login', 'is_social_active', 'profile_link'
    )
    list_filter = UserAdmin.list_filter + (
        'userprofile__is_social_active', HasProfileListFilter
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('userprofile')

    @admin.display(description='Approved', boolean=True, ordering='userprofile__is_social_active')
    def is_social_active(self, obj):
        try:
            return obj.userprofile.is_social_active
        except UserProfile.DoesNotExist:
            return None

    @admin.display(description='Profile')
    def profile_link(self, obj):
        try:
            profile = obj.userprofile
        except UserProfile.DoesNotExist:
            return '-'
        url = reverse('admin:accounts_userprofile_change', args=[profile.pk])
        return format_html('<a href="{}">{}</a>', url, profile)
