import logging

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django import forms
from registration.models import RegistrationProfile
from accounts.models import UserProfile

from edumanage.forms import UserProfileForm
from edumanage.models import Institution

logger = logging.getLogger(__name__)


@never_cache
def activate(request, activation_key):
    account = None
    if request.method == "GET":
        # Normalize before trying anything with it.
        activation_key = activation_key.lower()
        try:
            rp = RegistrationProfile.objects.get(activation_key=activation_key)
        except RegistrationProfile.DoesNotExist:
            return render(
                request,
                'registration/activate.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )
        try:
            user_profile = rp.user.get_profile()
        except UserProfile.DoesNotExist:
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
            queryset=User.objects.filter(pk=rp.user.pk), empty_label=None
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
            up = user.get_profile()
            up.institution = Institution.objects.get(
                pk=request_data['institution']
            )
            up.save()

        except:
            return render(
                request,
                'registration/activate_edit.html',
                {
                    'account': account,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
                }
            )
        # Normalize before trying anything with it.
        activation_key = activation_key.lower()
        try:
            rp = RegistrationProfile.objects.get(activation_key=activation_key)
            account = RegistrationProfile.objects.activate_user(activation_key)
            up.is_social_active = True
            up.save()
            logger.info('Activating user %s' % rp.user.username)
        except Exception as e:
            logger.info('An error occured: %s' % e)
            pass

        if account:
            # A user has been activated
            email = render_to_string(
                'registration/activation_complete.txt',
                {
                    'site': Site.objects.get_current(),
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
