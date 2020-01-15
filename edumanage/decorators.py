from django.template import RequestContext
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext as _
from accounts.models import User
from django import forms

from functools import wraps
from django.utils.decorators import available_attrs
from django.views.decorators.cache import (never_cache, cache_page)
from django.utils import six

from accounts.models import UserProfile
from edumanage.forms import UserProfileForm
from edumanage.models import Institution
from utils.edb_versioning import (
    edb_version_from_request,
    EDBVersionFromRequestException
)

# We only need get_nro_name from edumanage.views, but cannot import selectively
# as that would fail as a circular dependency
import edumanage.views

def social_active_required(function):
    @wraps(function, assigned=available_attrs(function))
    def wrap(request, *args, **kw):
        user = request.user
        try:
            profile = request.user.userprofile
            if profile.is_social_active is True:
                return function(request, *args, **kw)
            else:
                status = _(
                    "User account <strong>%(username)s</strong> is pending"
                    " activation. Administrators have been notified and will"
                    " activate this account within the next days. <br>If this"
                    " account has remained inactive for a long time contact"
                    " your technical coordinator or %(nroname)s Helpdesk") % {
                    'username': user.username,
                    'nroname': edumanage.views.get_nro_name(request.LANGUAGE_CODE)
                    }
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

def cache_page_ifreq(req_cache_func):
    def view_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def wrapped_view_func(request, *args, **kwargs):
            try:
                (cache_timeout, cache_kwargs) = req_cache_func(request,
                                                               *args,
                                                               **kwargs)
                ret = cache_page(cache_timeout, **cache_kwargs)(view_func)
            except TypeError:
                ret = never_cache(view_func)
            return ret(request, *args, **kwargs)
        return wrapped_view_func
    return view_decorator

def detect_eduroam_db_version(view):
    @wraps(view, assigned=available_attrs(view))
    def wrap(request, *args, **kwargs):
        try:
            version = edb_version_from_request(request, *args, **kwargs)
        except EDBVersionFromRequestException as exc:
            return HttpResponseBadRequest(six.text_type(exc))
        except ValueError:
            return HttpResponseBadRequest(
                'Could not determine a valid eduroam database version'
            )
        return view(request, version)
    return wrap
