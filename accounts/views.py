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
from django_registration.backends.activation.views import ActivationView
from django_registration.exceptions import ActivationError
from accounts.models import UserProfile

from edumanage.forms import UserProfileForm
from edumanage.models import Institution

logger = logging.getLogger(__name__)


@never_cache
def activate(request, activation_key):
    account = None
    if request.method == "GET":
        # Normalize before trying anything with it.
        activation_view = ActivationView()
        try:
            username = activation_view.validate_key(activation_key=activation_key)
        except ActivationError:
            return render(
                request,
                'registration/activate.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )
        try:
            # NOTE: This fix works for now but isn't that clean.
            # This is required because when a new user is created with google-oauth2,
            # they are marked with is_active = True, which will cause the call to
            # get_user to fail because it only works when is_active = False.
            temp_user = User.objects.get(username__exact=username)
            if temp_user.is_active:
                temp_user.is_active = False
                temp_user.save()
            user_profile = activation_view.get_user(username)
        except ActivationError:
            return render(
                request,
                'registration/activate.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )
        form = UserProfileForm(instance=user_profile)
        form.fields['user'] = forms.ModelChoiceField(
            queryset=User.objects.filter(pk=user_profile.pk), empty_label=None
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
        activation_view = ActivationView()
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
        try:
            username = activation_view.validate_key(activation_key=activation_key)
            account = activation_view.get_user(username)
            user.is_active = True
            user.save()
            up.is_social_active = True
            up.save()
            logger.info('Activating user {account}')
        except Exception as e:
            logger.info('POST: An error occured: %s' % e)
            pass

        if account:
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

        return render(
            request,
            'registration/activate.html',
            {
                'account': account,
                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
            }
        )
