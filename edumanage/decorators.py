from django.template import RequestContext
from django.shortcuts import render
from django.utils.translation import ugettext as _
from accounts.models import User
from django import forms

from accounts.models import UserProfile
from edumanage.forms import UserProfileForm
from edumanage.models import Institution


def social_active_required(function):
    def wrap(request, *args, **kw):
        user = request.user
        try:
            profile = request.user.userprofile
            if profile.is_social_active is True:
                return function(request, *args, **kw)
            else:
                status = _("User account <strong>%s</strong> is pending activation. Administrators have been notified and will activate this account within the next days. <br>If this account has remained inactive for a long time contact your technical coordinator or GRNET Helpdesk") %user.username
                return render(
                    request,
                    'status.html',
                    {
                        'status': status,
                        'inactive': True
                    },
                )
        except UserProfile.DoesNotExist:
            form = UserProfileForm()
            form.fields['user'] = forms.ModelChoiceField(
                queryset=User.objects.filter(pk=user.pk), empty_label=None
            )
            nomail = False
            if not user.email:
                nomail = True
                form.fields['email'] = forms.CharField()
            else:
                form.fields['email'] = forms.CharField(initial=user.email)
            form.fields['institution'] = forms.ModelChoiceField(
                queryset=Institution.objects.all(),
                empty_label=None
            )
            return render(
                request,
                'registration/select_institution.html',
                {
                    'form': form,
                    'nomail': nomail
                }
            )
    return wrap
