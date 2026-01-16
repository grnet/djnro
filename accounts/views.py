import logging

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from django.views.decorators.cache import never_cache
from django import forms
from django.core import signing
from accounts.models import UserProfile

from edumanage.forms import UserProfileForm
from edumanage.models import Institution

def get_user(username):
    try:
        user = User.objects.get(username__exact=username)
    except User.DoesNotExist:
        user = None

    return user

def render_activate_page(request, account):
    return render(
        request,
        'registration/activate.html',
        {
            'account': account,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
        }
    )

@never_cache
def activate(request, activation_key):
    account = None
    try:
        username = signing.loads(
            activation_key,
            salt=settings.REGISTRATION_SALT,
        )
    except signing.BadSignature:
        return render_activate_page(request, account)

    if request.method == "GET":

        user = get_user(username)
        if user is None:
            return render_activate_page(request, account)

        # NOTE: This fix works for now but isn't that clean.
        # This is required because when a new user is created with google-oauth2,
        # they are marked with is_active = True, which will cause the call to
        # get_user to fail because it only works when is_active = False.
        if user.is_active:
            user.is_active = False
            user.save()

        # Check if the user is already activated, which we do by checking the `is_social_active` value
        user_profile = user.userprofile
        if user_profile.is_social_active:
            return render_activate_page(request, account)

        form = UserProfileForm(instance=user.userprofile)
        form.fields['user'] = forms.ModelChoiceField(
            queryset=User.objects.filter(pk=user.pk), empty_label=None
        )
        form.fields['institution'] = forms.ModelChoiceField(
            queryset=Institution.objects.all(), empty_label=None
        )
        return render(
            request,
            'registration/activate_edit.html',
            {
                'account': account,
                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                'form': form
            }
        )
    if request.method == "POST":
        request_data = request.POST.copy()
        try:
            user = User.objects.get(pk=request_data['user'])
            up = user.userprofile
            up.institution = Institution.objects.get(
                pk=request_data['institution']
            )
            up.save()

        except Exception as e:
            return render(
                request,
                'registration/activate_edit.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )
        # Normalize before trying anything with it.
        account = get_user(username)
        if account is None:
            return render(
                request,
                'registration/activate_edit.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )

        user.is_active = True
        user.save()
        up.is_social_active = True
        up.save()

        # A user has been activated
        email = render_to_string(
            'registration/activation_complete.txt',
            {
                'site': get_current_site(request),
                'user': account
            }
        )
        send_mail(
            _('%sUser account activated') % settings.EMAIL_SUBJECT_PREFIX,
            email,
            settings.SERVER_EMAIL,
            account.email.split(';')
        )

        return render_activate_page(request, account)
