# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import json
import bz2
import math
import datetime
from xml.etree import ElementTree
import itertools
import locale
import requests

from django.shortcuts import redirect, render
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseBadRequest
)
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import logout as logout_view
from django import forms
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.core.mail.message import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from django.db.models import Max
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from django.utils import six
from accounts.models import User
from django.core.cache import cache
from django.contrib.auth import REDIRECT_FIELD_NAME

from edumanage.models import (
    ServiceLoc,
    InstRealmMon,
    InstitutionDetails,
    Realm,
    InstServer,
    URL_i18n,
    MonLocalAuthnParam,
    Institution,
    CatEnrollment,
    InstitutionContactPool,
    InstRealm,
    Contact,
    Name_i18n,
    Address_i18n,
    Coordinates,
    ERTYPES,
    ERTYPE_ROLES,
)
from .models import get_ertype_string
from accounts.models import UserProfile
from edumanage.forms import (
    InstDetailsForm,
    InstRealmForm,
    UserProfileForm,
    ContactForm,
    URL_i18nForm,
    MonLocalAuthnParamForm,
    InstRealmMonForm,
    ServiceLocForm,
    i18nFormSetDefaultLang,
    URL_i18nFormSet,
    InstServerForm
)
from registration.models import RegistrationProfile
from edumanage.decorators import (social_active_required,
                                  cache_page_ifreq,
                                  detect_eduroam_db_version)
from django.utils.cache import (
    get_max_age, patch_response_headers, patch_vary_headers
)
from django_dont_vary_on.decorators import dont_vary_on
from utils.cat_helper import CatQuery
from utils.locale import setlocale, compat_strxfrm
from utils.functional import partialclass


# Almost verbatim copy of django.views.i18n.set_language; however:
# * we avoid creating sessions for anonymous users
# * we want language selection to work even for requests that are not https;
#   for session storage this breaks when SESSION_COOKIE_SECURE=True, so we
#   always set a language cookie too
def set_language(request):
    """
    Redirect to a given url while setting the chosen language in the
    session and cookie. The session is written only for authenticated users.
    The url and the language code need to be specified in the request parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    """
    from django.views import i18n
    next = request.POST.get('next', request.GET.get('next'))
    if not i18n.is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')
        if not i18n.is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = HttpResponseRedirect(next)
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if lang_code and i18n.check_for_language(lang_code):
            if hasattr(request, 'session') and request.user.is_authenticated():
                request.session[i18n.LANGUAGE_SESSION_KEY] = lang_code
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code,
                                max_age=settings.LANGUAGE_COOKIE_AGE,
                                path=settings.LANGUAGE_COOKIE_PATH,
                                domain=settings.LANGUAGE_COOKIE_DOMAIN)
    return response


@never_cache
def index(request):
    return render(
        request,
        'front/index.html',
    )


@never_cache
def manage_login_front(request):
    user = request.user
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return render(
            request,
            'edumanage/welcome_manage.html',
            context=base_response(request)
        )
    except AttributeError:
        return render(
            request,
            'edumanage/welcome_manage.html',
            context={}
        )
    if user.is_authenticated() and user.is_active and profile.is_social_active:
        return redirect(reverse('manage'))
    else:
        return render(
            request,
            'edumanage/welcome_manage.html',
            context={}
        )


@login_required
@social_active_required
@never_cache
def manage(request):
    services_list = []
    servers_list = []
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return render(
            request,
            'edumanage/welcome.html',
            context=base_response(request)
        )
    services = ServiceLoc.objects.filter(institutionid=inst)
    services_list.extend([s for s in services])
    servers = InstServer.objects.filter(instid=inst)
    servers_list.extend([s for s in servers])
    return render(
        request,
        'edumanage/welcome.html',
        context=merge_dicts({
            'institution': inst,
            'services': services_list,
            'servers': servers_list,
        }, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def institutions(request):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    return render(
        request,
        'edumanage/institution.html',
        context=merge_dicts({
            'institution': inst,
        }, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_institution_details(request, institution_pk):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))

    if institution_pk and int(inst.pk) != int(institution_pk):
        messages.add_message(
            request,
            messages.ERROR,
            'You have no rights on this Institution'
        )
        return HttpResponseRedirect(reverse("institutions"))

    formset_params = (
        ('url', URL_i18n, {
            'formset': partialclass(URL_i18nFormSet,
                                    obj_descr=_('institution URL')),
            'min_num': 2,
            'validate_min': True,
        }),
        ('addr', Address_i18n, {
            'formset': partialclass(i18nFormSetDefaultLang,
                                    obj_descr=_('institution address')),
            'min_num': 1,
            'validate_min': True,
        }),
    )
    _fsf_kwargs = {'extra': 2}
    formsets = {}
    # Determine add or edit
    try:
        inst_details = InstitutionDetails.objects.get(institution=inst)
        form_kwargs = {'instance': inst_details}
    except InstitutionDetails.DoesNotExist:
        inst_details = None
        form_kwargs = {}
    form_fields = {
        'institution': forms.ModelChoiceField(
            queryset=Institution.objects.filter(pk=institution_pk),
            empty_label=None
        ),
        'contact': forms.ModelMultipleChoiceField(
            queryset=Contact.objects.filter(pk__in=getInstContacts(inst))
        ),
    }
    if request.method == "GET":
        form = InstDetailsForm(**form_kwargs)
        if not inst_details:
            form.fields['institution'] = form_fields['institution']
        form.fields['contact'] = form_fields['contact']
        for form_key, model, fsf_kwargs_bound in formset_params:
            fsf_kwargs = _fsf_kwargs.copy()
            fs_kwargs = {'prefix': '%ssform' % form_key}
            if inst_details:
                fsf_kwargs.update(fsf_kwargs_bound)
                fs_kwargs['instance'] = inst_details
            formsets[form_key] = generic_inlineformset_factory(
                model, **fsf_kwargs
            )(**fs_kwargs)
        return render(
            request,
            'edumanage/institution_edit.html',
            context=merge_dicts({
                'institution': inst,
                'form': form,
                'urls_form': formsets['url'],
                'addrs_form': formsets['addr']
            }, base_response(request))
        )
    if request.method == 'POST':
        request_data = request.POST.copy()
        form = InstDetailsForm(request_data, **form_kwargs)
        for form_key, model, fsf_kwargs_extra in formset_params:
            fsf_kwargs = _fsf_kwargs.copy()
            fsf_kwargs.update(fsf_kwargs_extra)
            fs_kwargs = {'prefix': '%ssform' % form_key}
            if inst_details:
                fs_kwargs.update(form_kwargs)
            formsets[form_key] = generic_inlineformset_factory(
                model, **fsf_kwargs
            )(request_data, **fs_kwargs)
        if form.is_valid() and all(
                [formsets[form_key].is_valid() for form_key in formsets]):
            instdets = form.save()
            for form_key in formsets:
                formsets[form_key].instance = instdets
                formsets[form_key].save()
            return HttpResponseRedirect(reverse("institutions"))
        # invalid form data, render page with errors
        form.fields.update(form_fields)
        return render(
            request,
            'edumanage/institution_edit.html',
            context=merge_dicts({
                'institution': inst,
                'form': form,
                'urls_form': formsets['url'],
                'addrs_form': formsets['addr']
            }, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def services(request, service_pk):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in ERTYPE_ROLES.SP:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Location. Your institution should be either SP or IdP/SP'
        )
        return render(
            request,
            'edumanage/services.html',
            context=merge_dicts({'institution': inst}, base_response(request))
        )
    try:
        services = ServiceLoc.objects.filter(institutionid=inst)
    except ServiceLoc.DoesNotExist:
        services = False

    if service_pk:
        try:
            services = services.get(pk=service_pk)
        except:
            messages.add_message(
                request,
                messages.ERROR,
                'You have no rights to view this location'
            )
            return HttpResponseRedirect(reverse("services"))
        return render(
            request,
            'edumanage/service_details.html',
            context=merge_dicts({
                'institution': inst,
                'service': services,
            }, base_response(request))
        )

    return render(
        request,
        'edumanage/services.html',
        context=merge_dicts({
            'institution': inst,
            'services': services,
        }, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_services(request, service_pk):
    user = request.user
    service = False
    edit = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in ERTYPE_ROLES.SP:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Service. Your institution should be either SP or IdP/SP'
        )
        return render(
            request,
            'edumanage/services_edit.html',
            context=merge_dicts({'edit': edit}, base_response(request))
        )
    formset_params = (
        ('url', URL_i18n, {
            'form': partialclass(URL_i18nForm,
                                 valid_urltypes='info'),
        }),
        ('name', Name_i18n, {
            'formset': partialclass(i18nFormSetDefaultLang,
                                    obj_descr=_('location name')),
            'extra': 1,
        }),
        ('addr', Address_i18n, {
            'formset': partialclass(i18nFormSetDefaultLang,
                                    obj_descr=_('institution address')),
            'min_num': 1,
            'validate_min': True,
        }),
    )
    _fsf_kwargs = {'extra': 2}
    formsets = {}
    # Determine add or edit
    try:
        service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
        form_kwargs = {'instance': service}
    except ServiceLoc.DoesNotExist:
        form_kwargs = {}
        if service_pk:
            messages.add_message(
                request,
                messages.ERROR,
                'You have no rights to edit this location'
            )
            return HttpResponseRedirect(reverse("services"))
    form_fields = {
        'institutionid': forms.ModelChoiceField(
            queryset=Institution.objects.filter(pk=inst.pk),
            empty_label=None
        ),
        'contact': forms.ModelMultipleChoiceField(
            queryset=Contact.objects.filter(pk__in=getInstContacts(inst)),
            required=False,
        ),
    }
    if request.method == "GET":
        form = ServiceLocForm(**form_kwargs)
        form.fields.update(form_fields)
        for form_key, model, fsf_kwargs_bound in formset_params:
            fsf_kwargs = _fsf_kwargs.copy()
            fs_kwargs = {'prefix': '%ssform' % form_key}
            if service:
                fsf_kwargs.update(fsf_kwargs_bound)
                fs_kwargs['instance'] = service
            formsets[form_key] = generic_inlineformset_factory(
                model, **fsf_kwargs)(**fs_kwargs)
        if service:
            edit = True
        return render(
            request,
            'edumanage/services_edit.html',
            context=merge_dicts({
                'form': form,
                'services_form': formsets['name'],
                'urls_form': formsets['url'],
                'addrs_form': formsets['addr'],
                "edit": edit
            }, base_response(request))
        )
    if request.method == 'POST':
        request_data = request.POST.copy()
        form = ServiceLocForm(request_data, **form_kwargs)
        for form_key, model, fsf_kwargs_extra in formset_params:
            fsf_kwargs = _fsf_kwargs.copy()
            fsf_kwargs.update(fsf_kwargs_extra)
            fs_kwargs = {'prefix': '%ssform' % form_key}
            if service:
                fs_kwargs.update(form_kwargs)
            formsets[form_key] = generic_inlineformset_factory(
                model, **fsf_kwargs
            )(request_data, **fs_kwargs)
        if form.is_valid() and all(
                [formsets[form_key].is_valid() for form_key in formsets]):
            serviceloc = form.save()
            service = serviceloc
            for form_key in formsets:
                formsets[form_key].instance = service
                formsets[form_key].save()
            return HttpResponseRedirect(reverse("services"))
        # invalid form data, render page with errors
        form.fields.update(form_fields)
        if service:
            edit = True
        return render(
            request,
            'edumanage/services_edit.html',
            context=merge_dicts({
                'institution': inst,
                'form': form,
                'services_form': formsets['name'],
                'urls_form': formsets['url'],
                'addrs_form': formsets['addr'],
                'edit': edit
            }, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_service(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        service_pk = req_data['service_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete service. Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            service = ServiceLoc.objects.get(
                institutionid=institution,
                pk=service_pk
            )
        except ServiceLoc.DoesNotExist:
            resp['error'] = "Could not get service or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            service.delete()
        except:
            resp['error'] = "Could not delete service"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Service successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def servers(request, server_pk):
    user = request.user
    servers = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        servers = InstServer.objects.filter(instid=inst)
    if server_pk:
        servers = servers.get(pk=server_pk)
        return render(
            request,
            'edumanage/server_details.html',
            context=merge_dicts({
                'institution': inst,
                'server': servers,
            }, base_response(request))
        )
    return render(
        request,
        'edumanage/servers.html',
        context=merge_dicts({
            'servers': servers
        }, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_server(request, server_pk):
    user = request.user
    server = False
    edit = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":
        # Determine add or edit
        try:
            server = InstServer.objects.get(instid=inst, pk=server_pk)
            form = InstServerForm(instance=server)
        except InstServer.DoesNotExist:
            form = InstServerForm()
            if server_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this server'
                )
                return HttpResponseRedirect(reverse("servers"))
        if server:
            edit = True

        return render(
            request,
            'edumanage/servers_edit.html',
            context=merge_dicts({
                'form': form,
                'edit': edit
            }, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:
            server = InstServer.objects.get(instid=inst, pk=server_pk)
            form = InstServerForm(request_data, instance=server)
            form.inst_list = server.instid.all()
        except InstServer.DoesNotExist:
            form = InstServerForm(request_data)
            form.inst_list = [inst]
            if server_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this server'
                )
                return HttpResponseRedirect(reverse("servers"))

        if form.is_valid():
            form.save()
            if not inst in form.instance.instid.all():
                form.instance.instid.add(inst)
            return HttpResponseRedirect(reverse("servers"))
        if server:
            edit = True
        return render(
            request,
            'edumanage/servers_edit.html',
            context=merge_dicts({
                'institution': inst,
                'form': form,
                'edit': edit
            }, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def cat_enroll(request):
    user = request.user
    cat_url = None
    inst_uid = None
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in ERTYPE_ROLES.IDP:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Enrollments. Your institution should be either IdP or IdP/SP'
        )
        return render(
            request,
            'edumanage/catenroll.html',
            context=merge_dicts({'status': False}, base_response(request))
        )
    if request.method == "GET":
        current_enrollments = inst.catenrollment_set.all()
        current_enrollments_list = current_enrollments.values_list(
            'cat_instance',
            flat=True
        )
        available_enrollments = [
            (x[0], x[1]) for x in settings.CAT_INSTANCES if x[0] not in current_enrollments_list
        ]
        if len(available_enrollments) == 0 and len(current_enrollments_list) == 0:
            messages.add_message(
                request,
                messages.ERROR,
                'There are no available CAT instances for your institution enrollment'
            )
            return render(
                request,
                'edumanage/catenroll.html',
                context=merge_dicts({'status': False}, base_response(request))
            )
        return render(
            request,
            'edumanage/catenroll.html',
            context=merge_dicts({
                'status': True,
                'current_enrollments': current_enrollments,
                'cat_instances': available_enrollments
            }, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        instance = request_data['catinstance']
        # Check if cat enrollment exists. It should not!
        if inst.catenrollment_set.filter(cat_instance=instance):
            messages.add_message(
                request,
                messages.ERROR,
                'There is already and enrollment for this CAT instance'
            )
            return HttpResponseRedirect(reverse("catenroll"))
        try:
            cat_instance = settings.CAT_AUTH[instance]
        except:
            messages.add_message(
                request,
                messages.ERROR,
                'Invalid CAT instance'
            )
            return HttpResponseRedirect(reverse("catenroll"))
        cat_api_key = cat_instance['CAT_API_KEY']
        cat_api_url = cat_instance['CAT_API_URL']

        enroll = CatQuery(cat_api_key, cat_api_url)
        params = {
            'NEWINST_PRIMARYADMIN': u"%s" % user.email,
            }
        cq_counter=1
        for iname in inst.org_name.all():
            params['option[S%d]' % cq_counter] = 'general:instname'
            params['value[S%d-0]' % cq_counter] = iname.name
            params['value[S%d-lang]' % cq_counter] = iname.lang
            cq_counter += 1
            if iname.lang == 'en':
                params['option[S%d]' % cq_counter] = 'general:instname'
                params['value[S%d-0]' % cq_counter] = iname.name
                params['value[S%d-lang]' % cq_counter] = 'C'
                cq_counter += 1
        newinst = enroll.newinst(params)
        cat_url = None
        inst_uid = None
        if newinst:
            # this should be True only for successful postings
            status = enroll.status
            response = enroll.response
            inst_uid = response['inst_unique_id']
            cat_url = response['enrollment_URL']
            catentry = CatEnrollment()
            catentry.cat_inst_id = inst_uid
            catentry.inst = inst
            catentry.url = cat_url
            catentry.applier = user
            catentry.cat_instance = instance
            catentry.save()
            # We should notify the user
        else:
            status = enroll.status
            response = enroll.response
        return render(
            request,
            'edumanage/catenroll.html',
            context=merge_dicts({
                'status': True,
                'response_status': status,
                'response': response,
                'cat_url': cat_url,
                'inst_uid': inst_uid
            }, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_server(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        server_pk = req_data['server_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete server. Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            server = InstServer.objects.get(instid=institution, pk=server_pk)
        except InstServer.DoesNotExist:
            resp['error'] = "Could not get server or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            server.delete()
        except:
            resp['error'] = "Could not delete server"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Server successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def realms(request):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        realms = InstRealm.objects.filter(instid=inst)
    if inst.ertype not in ERTYPE_ROLES.IDP:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Realms. Your institution should be either IdP or IdP/SP'
        )
    return render(
        request,
        'edumanage/realms.html',
        context=merge_dicts({'realms': realms}, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_realm(request, realm_pk):
    user = request.user
    realm = False
    edit = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in ERTYPE_ROLES.IDP:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Realm. Your institution should be either IdP or IdP/SP')
        return render(
            request,
            'edumanage/realms_edit.html',
            context=merge_dicts({'edit': edit}, base_response(request))
        )
    if request.method == "GET":

        # Determine add or edit
        try:
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm()
            if realm_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this realm'
                )
                return HttpResponseRedirect(reverse("realms"))
        form.fields['instid'] = forms.ModelChoiceField(
            queryset=Institution.objects.filter(pk=inst.pk),
            empty_label=None
        )
        form.fields['proxyto'] = forms.ModelMultipleChoiceField(
            queryset=InstServer.objects.filter(
                pk__in=getInstServers(inst, True)
            )
        )
        if realm:
            edit = True
        return render(
            request,
            'edumanage/realms_edit.html',
            context=merge_dicts({'form': form, 'edit': edit}, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(request_data, instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm(request_data)
            if realm_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this realm'
                )
                return HttpResponseRedirect(reverse("realms"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("realms"))
        else:
            form.fields['instid'] = forms.ModelChoiceField(
                queryset=Institution.objects.filter(pk=inst.pk),
                empty_label=None
            )
            form.fields['proxyto'] = forms.ModelMultipleChoiceField(
                queryset=InstServer.objects.filter(
                    pk__in=getInstServers(inst, True)
                )
            )
        if realm:
            edit = True
        return render(
            request,
            'edumanage/realms_edit.html',
            context=merge_dicts({'institution': inst, 'form': form, 'edit': edit}, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_realm(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        realm_pk = req_data['realm_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            realm = InstRealm.objects.get(instid=institution, pk=realm_pk)
        except InstRealm.DoesNotExist:
            resp['error'] = "Could not get realm or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            realm.delete()
        except:
            resp['error'] = "Could not delete realm"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Realm successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def contacts(request):
    user = request.user
    instcontacts = []
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        instcontacts.extend([
            x.contact.pk for x in InstitutionContactPool.objects.filter(
                institution=inst
            )
        ])
        contacts = Contact.objects.filter(pk__in=instcontacts)
    return render(
        request,
        'edumanage/contacts.html',
        context=merge_dicts({'contacts': contacts}, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_contact(request, contact_pk):
    user = request.user
    edit = False
    contact = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":

        # Determine add or edit
        try:
            contactinst = InstitutionContactPool.objects.get(
                institution=inst,
                contact__pk=contact_pk
            )
            contact = contactinst.contact
            form = ContactForm(instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm()
            if contact_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this contact'
                )
                return HttpResponseRedirect(reverse("contacts"))
        if contact:
            edit = True
        return render(
            request,
            'edumanage/contacts_edit.html',
            context=merge_dicts({
                'form': form,
                'edit': edit
            }, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:
            contactinst = InstitutionContactPool.objects.get(
                institution=inst,
                contact__pk=contact_pk
            )
            contact = contactinst.contact
            form = ContactForm(request_data, instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm(request_data)
            if contact_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this contact'
                )
                return HttpResponseRedirect(reverse("contacts"))

        if form.is_valid():
            contact = form.save()
            inst_cont_pool, created = InstitutionContactPool.objects.get_or_create(
                contact=contact,
                institution=inst
            )
            inst_cont_pool.save()
            return HttpResponseRedirect(reverse("contacts"))
        if contact:
            edit = True
        return render(
            request,
            'edumanage/contacts_edit.html',
            context=merge_dicts({'form': form, "edit": edit}, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_contact(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        contact_pk = req_data['contact_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete contact. Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            contactinst = InstitutionContactPool.objects.get(
                institution=institution,
                contact__pk=contact_pk
            )
            contact = contactinst.contact
        except InstitutionContactPool.DoesNotExist:
            resp['error'] = "Could not get contact or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            for service in ServiceLoc.objects.filter(institutionid=institution):
                if (
                    contact in service.contact.all() and
                    len(service.contact.all()) == 1
                ):
                    resp['error'] = "Could not delete contact. " \
                        "It is the only contact in service <b>%s</b>." \
                        "<br>Fix it and try again" % \
                        service.get_name(lang="en")
                    return HttpResponse(
                        json.dumps(resp),
                        content_type='application/json'
                    )
            if (
                contact in institution.institutiondetails.contact.all() and
                len(institution.institutiondetails.contact.all()) == 1
            ):
                resp['error'] = "Could not delete contact. It is the" \
                    " only contact your institution has.<br>Fix it and try again"
                return HttpResponse(
                    json.dumps(resp),
                    content_type='application/json'
                )
            contact.delete()
        except Exception:
            resp['error'] = "Could not delete contact"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def instrealmmon(request):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        instrealmmons = InstRealmMon.objects.filter(realm__instid=inst)
    return render(
        request,
        'edumanage/instrealmmons.html',
        context=merge_dicts({'realms': instrealmmons}, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_instrealmmon(request, instrealmmon_pk):
    user = request.user
    instrealmmon = False
    edit = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":
        # Determine add or edit
        try:
            instrealmmon = InstRealmMon.objects.get(
                pk=instrealmmon_pk,
                realm__instid=inst
            )
            form = InstRealmMonForm(instance=instrealmmon)
        except InstRealmMon.DoesNotExist:
            form = InstRealmMonForm()
            if instrealmmon_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm'
                )
                return HttpResponseRedirect(reverse("instrealmmon"))
        if instrealmmon:
            edit = True
        form.fields['realm'] = forms.ModelChoiceField(
            queryset=InstRealm.objects.filter(instid=inst.pk).exclude(
                realm__startswith="*"
            ),
            empty_label=None
        )
        return render(
            request,
            'edumanage/instrealmmon_edit.html',
            context=merge_dicts({'form': form, 'edit': edit}, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:
            instrealmmon = InstRealmMon.objects.get(
                pk=instrealmmon_pk,
                realm__instid=inst
            )
            form = InstRealmMonForm(request_data, instance=instrealmmon)
        except InstRealmMon.DoesNotExist:
            form = InstRealmMonForm(request_data)
            if instrealmmon_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm'
                )
                return HttpResponseRedirect(reverse("instrealmmon"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("instrealmmon"))
        if instrealmmon:
            edit = True
        form.fields['realm'] = forms.ModelChoiceField(
            queryset=InstRealm.objects.filter(instid=inst.pk).exclude(
                realm__startswith="*"
            ),
            empty_label=None
        )
        return render(
            request,
            'edumanage/instrealmmon_edit.html',
            context=merge_dicts({'form': form, "edit": edit}, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_instrealmmon(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        instrealmmon_pk = req_data['instrealmmon_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete monitored realm. Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            instrealmmon = InstRealmMon.objects.get(
                pk=instrealmmon_pk,
                realm__instid=institution
            )
            instrealmmon.delete()
        except InstRealmMon.DoesNotExist:
            resp['error'] = "Could not get monitored realm or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def add_monlocauthpar(request, instrealmmon_pk, monlocauthpar_pk):
    user = request.user
    monlocauthpar = False
    edit = False
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":
        # Determine add or edit
        try:
            instrealmmon = InstRealmMon.objects.get(
                pk=instrealmmon_pk,
                realm__instid=inst
            )
            monlocauthpar = MonLocalAuthnParam.objects.get(
                pk=monlocauthpar_pk,
                instrealmmonid__realm__instid=inst
            )
            form = MonLocalAuthnParamForm(instance=monlocauthpar)
        except MonLocalAuthnParam.DoesNotExist:
            form = MonLocalAuthnParamForm()
            if monlocauthpar_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm Parameters'
                )
                return HttpResponseRedirect(reverse("instrealmmon"))
        except InstRealmMon.DoesNotExist:
            if instrealmmon_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm Parameters'
                )
            return HttpResponseRedirect(reverse("instrealmmon"))
        if monlocauthpar:
            edit = True
        form.fields['instrealmmonid'] = forms.ModelChoiceField(
            queryset=InstRealmMon.objects.filter(pk=instrealmmon.pk),
            empty_label=None
        )
        return render(
            request,
            'edumanage/monlocauthpar_edit.html',
            context=merge_dicts({'form': form,"edit" : edit, "realm":instrealmmon}, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:
            instrealmmon = InstRealmMon.objects.get(
                pk=instrealmmon_pk,
                realm__instid=inst
            )
            monlocauthpar = MonLocalAuthnParam.objects.get(
                pk=monlocauthpar_pk,
                instrealmmonid__realm__instid=inst
            )
            form = MonLocalAuthnParamForm(request_data, instance=monlocauthpar)
        except MonLocalAuthnParam.DoesNotExist:
            form = MonLocalAuthnParamForm(request_data)
            if monlocauthpar_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm Parameters'
                )
                return HttpResponseRedirect(reverse("instrealmmon"))
        except InstRealmMon.DoesNotExist:
            if instrealmmon_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this Monitoring Realm Parameters'
                )
            return HttpResponseRedirect(reverse("instrealmmon"))
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("instrealmmon"))
        if monlocauthpar:
            edit = True
        form.fields['instrealmmonid'] = forms.ModelChoiceField(
            queryset=InstRealmMon.objects.filter(pk=instrealmmon.pk),
            empty_label=None
        )
        return render(
            request,
            'edumanage/monlocauthpar_edit.html',
            context=merge_dicts({'form': form, "edit": edit, "realm":instrealmmon}, base_response(request))
        )


@login_required
@social_active_required
@never_cache
def del_monlocauthpar(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        monlocauthpar_pk = req_data['monlocauthpar_pk']
        resp = {}
        try:
            profile = user.userprofile
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete realm monitoring parameters. Not enough rights"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        try:
            monlocauthpar = MonLocalAuthnParam.objects.get(
                pk=monlocauthpar_pk,
                instrealmmonid__realm__instid=institution
            )
            monlocauthpar.delete()
        except MonLocalAuthnParam.DoesNotExist:
            resp['error'] = "Could not get realm monitoring parameters or you have no rights to delete"
            return HttpResponse(json.dumps(resp), content_type='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
@social_active_required
@never_cache
def adduser(request):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))

    if request.method == "GET":
        form = ContactForm()
        return render(
            request,
            'edumanage/add_user.html',
            context=merge_dicts({'form': form}, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        form = ContactForm(request_data)
        if form.is_valid():
            contact = form.save()
            inst_cont_pool = InstitutionContactPool(
                contact=contact,
                institution=inst
            )
            inst_cont_pool.save()
            response_data = {}
            response_data['value'] = "%s" % contact.pk
            response_data['text'] = "%s" % contact
            return HttpResponse(
                json.dumps(response_data),
                content_type='application/json'
            )
        else:
            return render(
                request,
                'edumanage/add_user.html',
                context=merge_dicts({'form': form}, base_response(request))
            )


@login_required
@social_active_required
def base_response(request):
    user = request.user
    inst = []
    server = []
    services = []
    instrealms = []
    instcontacts = []
    contacts = []
    institution = False
    institution_exists = False
    institution_canhaveservicelocs = False
    try:
        profile = user.userprofile
        institution = profile.institution
        institution_exists = True
    except UserProfile.DoesNotExist:
        institution_exists = False
    try:
        inst.append(institution)
        server = InstServer.objects.filter(instid=institution)
        services = ServiceLoc.objects.filter(institutionid=institution)
        instrealms = InstRealm.objects.filter(instid=institution)
        instcontacts.extend([
            x.contact.pk for x in InstitutionContactPool.objects.filter(
                institution=institution
            )
        ])
        contacts = Contact.objects.filter(pk__in=instcontacts)
        instrealmmons = InstRealmMon.objects.filter(realm__instid=institution)
    except:
        pass
    try:
        instututiondetails = institution.institutiondetails
    except:
        instututiondetails = False
    try:
        institution_canhaveservicelocs = institution.ertype in ERTYPE_ROLES.SP
    except:
        pass
    return {
        'inst_num': len(inst),
        'servers_num': len(server),
        'services_num': len(services),
        'realms_num': len(instrealms),
        'contacts_num': len(contacts),
        'monrealms_num': len(instrealmmons),
        'institution': institution,
        'institutiondetails': instututiondetails,
        'institution_exists': institution_exists,
        'institution_canhaveservicelocs': institution_canhaveservicelocs,
        'ERTYPES': ERTYPES,
        'ERTYPE_ROLES': ERTYPE_ROLES,
    }


@login_required
@social_active_required
@never_cache
def get_service_points(request):
    lang = request.LANGUAGE_CODE
    if request.method == "GET":
        user = request.user
        try:
            profile = user.userprofile
            inst = profile.institution
        except UserProfile.DoesNotExist:
            inst = False
            return HttpResponseNotFound('<h1>Something went really wrong</h1>')
        servicelocs = localizePointNames(ourPoints(institution=inst), lang)
        return HttpResponse(json.dumps(servicelocs), content_type='application/json')
    else:
        return HttpResponseNotFound('<h1>Something went really wrong</h1>')


@login_required
@never_cache
def overview(request):
    user = request.user
    if user.has_perm('accounts.overview'):
        users = User.objects.all()
        institutions = Institution.objects.all()
        return render(
            request,
            'overview/index.html',
            context={'users': users, 'institutions': institutions}
        )
    else:
        return render(
            request,
            'overview/index.html',
            context={'violation': True}
        )


@never_cache
def get_all_services(request):
    lang = request.LANGUAGE_CODE
    locs = localizePointNames(ourPoints(), lang)
    return HttpResponse(json.dumps(locs), content_type='application/json')


@never_cache
def manage_login(request, backend):
    logout(request)
    qs = request.GET.urlencode()
    qs = '?%s' % qs if qs else ''
    if backend == 'shibboleth':
        return redirect(reverse('login') + qs)
    if backend == 'locallogin':
        return redirect(reverse('altlogin') + qs)
    return redirect(reverse('social:begin', args=[backend]) + qs)


@never_cache
def user_login(request):
    try:
        errors = []
        error = ''
        username = lookupShibAttr(settings.SHIB_USERNAME, request.META)
        firstname = lookupShibAttr(settings.SHIB_FIRSTNAME, request.META)
        lastname = lookupShibAttr(settings.SHIB_LASTNAME, request.META)
        mail = lookupShibAttr(settings.SHIB_MAIL, request.META)
        entitlement = lookupShibAttr(settings.SHIB_ENTITLEMENT, request.META)

        if not username:
            errors.append(
                _("Your idP should release the eduPersonPrincipalName attribute towards this service<br>")
            )

        if settings.SHIB_AUTH_ENTITLEMENT:
            if settings.SHIB_AUTH_ENTITLEMENT not in entitlement.split(";"):
                errors.append(
                    _("Your idP should release an appropriate eduPersonEntitlement attribute towards this service<br>")
                )

        if not mail:
            errors.append(
                _("Your idP should release the mail attribute towards this service")
            )

        if errors:
            error = ''.join(errors)
            return render(
                request,
                'status.html',
                context={'error': error, "missing_attributes": True}
            )

        try:
            user = User.objects.get(username__exact=username)
            user.email = mail
            user.first_name = firstname
            user.last_name = lastname
            user.save()
        except User.DoesNotExist:
            pass

        user = authenticate(username=username, firstname=firstname, lastname=lastname, mail=mail, authsource='shibboleth')
        request.session['SHIB_LOGOUT'] = hasattr(settings, 'SHIB_LOGOUT_URL')
        if user is not None:
            try:
                profile = user.userprofile
                profile.institution
            except UserProfile.DoesNotExist:
                form = UserProfileForm()
                form.fields['user'] = forms.ModelChoiceField(
                    queryset=User.objects.filter(pk=user.pk),
                    empty_label=None
                )
                form.fields['institution'] = forms.ModelChoiceField(
                    queryset=Institution.objects.all(),
                    empty_label=None
                )
                form.fields['email'] = forms.CharField(initial=user.email)
                return render(
                    request,
                    'registration/select_institution.html',
                    context={'form': form}
                )

            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(
                    request.GET.get(REDIRECT_FIELD_NAME,
                                    default=reverse('manage'))
                )
            else:
                status = _(
                    "User account <strong>%(username)s</strong> is pending"
                    " activation. Administrators have been notified and will"
                    " activate this account within the next days. <br>If this"
                    " account has remained inactive for a long time contact"
                    " your technical coordinator or %(nroname)s Helpdesk") % {
                    'username': user.username,
                    'nroname': get_nro_name(request.LANGUAGE_CODE)
                    }

                return render(
                    request,
                    'status.html',
                    context={'status': status, 'inactive': True}
                )
        else:
            error = _(
                "Something went wrong during user authentication."
                " Contact your administrator %s" % user
            )
            return render(
                request,
                'status.html',
                context={'error': error}
            )
    except Exception as e:
        error = _("Invalid login procedure. Error: %s" % e)
        return render(
            request,
            'status.html',
            context={'error': error}
        )


@never_cache
def user_logout(request, **kwargs):
    shib_logout_url = getattr(settings, 'SHIB_LOGOUT_URL', None)
    if 'return' in request.GET and \
            'action' in request.GET and \
            request.GET.get('action') == 'logout':
        request_data = request.GET.copy()
        request_data[REDIRECT_FIELD_NAME] = request_data.get('return')
        del request_data['return']
        del request_data['action']
        request.GET = request_data
    elif shib_logout_url is not None and \
            request.session.get('SHIB_LOGOUT') is True:
        kwargs['next_page'] = shib_logout_url
    return logout_view(request, **kwargs)


@never_cache
def geolocate(request):
    return render(
        request,
        'front/geolocate.html',
        context={}
    )


@never_cache
def api(request):
    current_site = get_current_site(request)
    return render(
        request,
        'front/api.html',
        context={'site': current_site}
    )


@never_cache
def participants(request):
    institutions = Institution.objects.filter(institutiondetails__isnull=False).\
      select_related('institutiondetails')
    cat_instance = 'production'
    dets = []
    cat_exists = False
    for i in institutions:
        dets.append(i.institutiondetails)
        if i.get_active_cat_enrl(cat_instance):
            cat_exists = True
    with setlocale((request.LANGUAGE_CODE, 'UTF-8'), locale.LC_COLLATE):
        dets.sort(key=lambda x: compat_strxfrm(
            x.institution.get_name(lang=request.LANGUAGE_CODE)))
    return render(
        request,
        'front/participants.html',
        context={
            'institutions': dets,
            'catexists': cat_exists
        }
    )


@never_cache
def connect(request):
    institutions = Institution.objects.filter(ertype__in=ERTYPE_ROLES.IDP,
                                              institutiondetails__isnull=False).\
        select_related('institutiondetails')
    cat_instance = 'production'
    dets = []
    dets_cat = {}
    cat_exists = False
    for i in institutions:
        dets.append(i.institutiondetails)
        catids = i.get_active_cat_ids(cat_instance)
        if len(catids):
            cat_exists = True
            # only use first inst+CAT binding (per CAT instance), even if there
            # may be more
            dets_cat[i.pk] = catids[0]
    with setlocale((request.LANGUAGE_CODE, 'UTF-8'), locale.LC_COLLATE):
        dets.sort(key=lambda x: compat_strxfrm(
            x.institution.get_name(lang=request.LANGUAGE_CODE)))
    if settings_dict_get('CAT_AUTH', cat_instance) is None:
        cat_exists = False
        cat_api_direct = None
        cat_api_ldlbase = None
        cat_api_version = None
    else:
        cat_api_direct = settings_dict_get('CAT_AUTH', cat_instance,
                                           'CAT_USER_API_URL')
        cat_api_version = settings_dict_get('CAT_AUTH', cat_instance,
                                           'CAT_USER_API_VERSION',
                                            default=2)
        if cat_api_direct is None:
            cat_exists = False
            cat_api_ldlbase = None
        else:
            cat_api_ldlbase = settings_dict_get('CAT_AUTH', cat_instance,
                                                'CAT_USER_API_LOCAL_DOWNLOADS')
            if not cat_api_ldlbase and cat_api_direct:
                cat_api_ldlbase = cat_api_direct.replace('user/API.php', '')
    template = settings_dict_get('CAT_CONNECT_TEMPLATE', cat_instance)
    return render(
        request,
        template or 'front/connect.html',
        context={
            'institutions': dets,
            'institutions_cat': dets_cat,
            'catexists': cat_exists,
            'cat_api_direct': cat_api_direct,
            'cat_api_ldlbase': cat_api_ldlbase,
            'cat_api_version': cat_api_version
        }
    )


@never_cache
def selectinst(request):
    if request.method == 'POST':
        request_data = request.POST.copy()
        user = request_data['user']
        try:
            UserProfile.objects.get(user=user)
            error = _("Violation warning: User account is already associated with an institution.The event has been logged and our administrators will be notified about it")
            return render(
                request,
                'status.html',
                context={'error': error, 'inactive': True}
            )
        except UserProfile.DoesNotExist:
            pass

        form = UserProfileForm(request_data)
        if form.is_valid():
            mailField = form.cleaned_data.pop('email')
            userprofile = form.save()
            useradded = userprofile.user
            useradded.email = mailField
            useradded.save()
            user_activation_notify(request, userprofile)
            error = _(
                "User account <strong>%(username)s</strong> is pending activation."
                " Administrators have been notified and will activate "
                "this account within the next days. <br>If this account"
                " has remained inactive for a long time contact your technical"
                " coordinator or %(nroname)s Helpdesk") % {
                'username': userprofile.user.username,
                'nroname': get_nro_name(request.LANGUAGE_CODE)
                }
            return render(
                request,
                'status.html',
                context={'status': error, 'inactive': True}
            )
        else:
            form.fields['user'] = forms.ModelChoiceField(
                queryset=User.objects.filter(pk=user),
                empty_label=None
            )
            form.fields['institution'] = forms.ModelChoiceField(
                queryset=Institution.objects.all(),
                empty_label=None
            )
            nomail = False
            user_obj = User.objects.get(pk=user)
            if not user_obj.email:
                nomail = True
                form.fields['email'] = forms.CharField()
            else:
                form.fields['email'] = forms.CharField(initial=user_obj.email)
            return render(
                request,
                'registration/select_institution.html',
                context={'form': form, 'nomail': nomail}
            )

    else:
        return HttpResponseBadRequest('<h1>Only POST requests are allowed at this URL.</h1>')

def user_activation_notify(request, userprofile):
    current_site = get_current_site(request)
    subject = render_to_string(
        'registration/activation_email_subject.txt',
        {'site': current_site}
    )
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    registration_profile = RegistrationProfile.objects.create_profile(userprofile.user)
    message = render_to_string(
        'registration/activation_email.txt',
        {
            'activation_key': registration_profile.activation_key,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
            'site': current_site,
            'user': userprofile.user,
            'institution': userprofile.institution
        })
    send_new_mail(
        settings.EMAIL_SUBJECT_PREFIX + subject,
        message, settings.SERVER_EMAIL,
        settings.NOTIFY_ADMIN_MAILS, []
    )


@never_cache
def closest(request):
    if request.method == 'GET':
        request_data = request.GET.copy()
        response_location = {}
        if 'lat' in request.GET and 'lng' in request.GET:
            response_location["lat"] = request_data['lat']
            response_location["lng"] = request_data['lng']
        else:
            response = {
                "status": "Cannot parse a request without longitude or latitude. Use ?lng=<langitude>&lat=<latitude>&_=<random_num> in your query"
            }
            return HttpResponse(
                json.dumps(response),
                content_type='application/json'
            )
        try:
            lat = float(request_data.get('lat'))
            lng = float(request_data.get('lng'))
        except ValueError:
            return HttpResponseBadRequest()
        R = 6371
        distances = {}
        closestMarker = {}
        closest = -1
        points = getPoints()
        for (counter, i) in enumerate(points):
            pointname = i['text']
            pointlng = i['lng']
            pointlat = i['lat']
            pointtext = i['text']
            plainname = i['name']
            dLat = rad(float(pointlat) - float(lat))
            dLong = rad(float(pointlng) - float(lng))
            a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(rad(lat)) *\
                math.cos(rad(float(pointlat))) * math.sin(dLong / 2) *\
                math.sin(dLong / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            d = R * c
            distances[counter] = d
            if (closest == -1 or d < distances[closest]):
                closest = counter
                closestMarker = {
                    'name': pointname,
                    'lat': pointlat,
                    'lng': pointlng,
                    'text': pointtext,
                    'plainname': plainname
                }
        return HttpResponse(
            json.dumps(closestMarker),
            content_type='application/json'
        )
    else:
        response = {
            "status": "Use a GET method for your request"
        }
        return HttpResponse(json.dumps(response), content_type='application/json')


@never_cache
def worldPoints(request):
    if request.method == 'GET':
        points = getPoints()
        return HttpResponse(json.dumps(points), content_type='application/json')


@never_cache
def world(request):
        return render(
            request,
            'front/world.html',
            context={}
        )


@never_cache
def managementPage(request):
    return render(
        request,
        'front/management.html',
        context={}
    )


def getPoints():
    points = cache.get('points')
    if points:
        points = bz2.decompress(points)
        if six.PY3:
            # decode from bytes to strings
            # (done automatically in json.loads on python 3.6+)
            points = points.decode('utf-8')
        return json.loads(points)
    else:
        point_list = []
        doc = ElementTree.parse(settings.KML_FILE)
        root = doc.getroot()
        r = root.getchildren()[0]
        for (counter, i) in enumerate(r.getchildren()):
            if "id" in i.keys():
                j = i.getchildren()
                pointname = j[0].text
                point = j[2].getchildren()[0].text
                pointlng, pointlat, pointele = point.split(',')
                marker = {
                    "name": pointname,
                    "lat": pointlat,
                    "lng": pointlng,
                    "text": j[1].text
                }
                point_list.append(marker)
        points = json.dumps(point_list)
        # make timeout configurable
        # encode points into bytestring on python 3, keep as-is otherwise
        cache.set('points', bz2.compress(points.encode('utf-8') if six.PY3 else points), 60 * 60 * 24)
        return json.loads(points)


def ourPoints(institution=None, cache_flush=False):
    # make this configurable
    cache_timeout = 60 * 60

    def cache_key(inst_key):
        # make this configurable
        return 'ourpoints:%d' % int(inst_key)

    if not isinstance(institution, Institution):
        institution = None

    cache_keys = {}
    institutions = {}

    if institution is not None:
        cache_keys[institution.pk] = cache_key(institution.pk)
        institutions[institution.pk] = institution
        # not really necessary, formally introduced in Django 1.10
        # from django.db.models.query import prefetch_related_objects
        # prefetch_related_objects([institution], ['org_name'])
    else:
        for i in Institution.objects.all().prefetch_related('org_name'):
            cache_keys[i.pk] = cache_key(i.pk)
            institutions[i.pk] = i

    points = {}

    if cache_flush:
        cache.delete_many(cache_keys.values())
    else:
        points = cache.get_many(cache_keys.values())

    points_ret = []
    keys_tocache = []

    for inst_pk in institutions:
        cache_key = cache_keys[inst_pk]
        try:
            # points_ret.extend(json.loads(bz2.decompress(points[cache_key])))
            points_ret.extend(json.loads(points[cache_key]))
            continue
        except KeyError:
            keys_tocache.append(cache_key)

        servicelocs = ServiceLoc.objects\
          .filter(institutionid=institutions[inst_pk])\
          .prefetch_related('loc_name')
          # .prefetch_related('loc_name', 'contact')
        inst_names = { name.lang: name.name for name in
                           institutions[inst_pk].org_name.all() }

        points[cache_key] = []

        for sl in servicelocs:
            point = {}
            point['lat'] = u"%s" % sl.latitude
            point['lng'] = u"%s" % sl.longitude
            addrs = {
                lang: [
                    ', '.join([f for f in (addr.street, addr.city) if f])
                    for addr in group
                ]
                for lang, group in itertools.groupby(
                    sl.address.order_by('lang'),
                    key=lambda addr: addr.lang
                )
            }
            point['address'] = {
                lang: '<br>'.join(addrs[lang])
                for lang in addrs
            }
            if sl.enc_level:
                point['enc'] = u"%s" % (
                    ','.join(sl.enc_level)
                    )
            else:
                point['enc'] = u"-"
            point['AP_no'] = u"%s" % (sl.AP_no)
            point['inst'] = inst_names
            point['inst_key'] = u"%s" % inst_pk
            point['name'] = { name.lang: name.name for name in
                                  sl.loc_name.all() }
            # point['contacts'] = [
            #     { attr: getattr(contact, attr, '')
            #       for attr in ['name', 'phone', 'email'] }
            #     for contact in sl.contact.all()
            #     ]
            for loc_tag, __ in ServiceLoc.LOCATION_TAGS:
                point[loc_tag] = str(loc_tag in sl.tag)
            point['wired_no'] = u"%s" % (sl.wired_no)
            point['SSID'] = u"%s" % (sl.SSID)
            point['key'] = u"%s" % sl.pk
            points[cache_key].append(point)

        points_ret.extend(points[cache_key])

    if len(keys_tocache):
        # cache.set_many({key: bz2.compress(json.dumps(points[key]))
        #                     for key in keys_tocache},
        #                    cache_timeout)
        cache.set_many({key: json.dumps(points[key]) for key in keys_tocache},
                           cache_timeout)

    return points_ret


def localizePointNames(points, lang='en'):
    for point in points:
        for key in ['inst', 'name', 'address']:
            if key not in point:
                continue
            try:
                point[key] = point[key][lang]
            except KeyError:
                point[key] = point[key].get('en', 'unknown')
    return points


def xml_address_elements(elem, obj, version):
    addr_objs = obj.address.all()
    if version.is_version_1:
        addr_objs = addr_objs.filter(lang="en")[:1]
    for addr_obj in addr_objs:
        addr_elem = ElementTree.SubElement(elem, "address")
        for prop in ["street", "city"]:
            prop_elem = ElementTree.SubElement(addr_elem, prop)
            prop_elem.text = getattr(addr_obj, prop)
            if version.is_version_2:
                prop_elem.attrib["lang"] = addr_obj.lang

def xml_coordinates_elements(elem, obj, version):
    if version.is_version_1 and not isinstance(obj, ServiceLoc):
        return
    coord_objs = obj.coordinates
    if isinstance(coord_objs, Coordinates):
        coord_objs = [coord_objs]
    elif coord_objs is None:
        coord_objs = []
    else:
        coord_objs = coord_objs.all()
    coords_elem_vals = []
    coordinate_fields = [f.name for f in Coordinates._meta.get_fields()
                         if not f.auto_created]
    for coord_obj in coord_objs:
        if version.is_version_1:
            for prop in coordinate_fields[:2]:
                prop_elem = ElementTree.SubElement(elem, prop)
                prop_elem.text = six.text_type(getattr(coord_obj, prop))
            break # only render the first coord_obj
        else:
            coords_elem_vals.append(','.join([
                six.text_type(prop)
                for prop in [
                    getattr(coord_obj, attr)
                    for attr in coordinate_fields
                ]
                if prop is not None
            ]))
    if coords_elem_vals:
        coords_elem = ElementTree.SubElement(elem, "coordinates")
        coords_elem.text = ';'.join(coords_elem_vals)

@never_cache
@detect_eduroam_db_version
def instxml(request, version):
    ElementTree._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ElementTree.Element("institutions")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "noNamespaceSchemaLocation", "institution.xsd")
    institutions = Institution.objects.all().select_related(
        'institutiondetails', 'realmid'
    ).prefetch_related(
        'org_name', 'institutiondetails__contact',
        'institutiondetails__address', 'institutiondetails__coordinates',
        'institutiondetails__url', 'instrealm_set')
    servicelocs = ServiceLoc.objects.all().prefetch_related(
        'coordinates', 'loc_name', 'address', 'contact', 'url'
    ).order_by('institutionid')
    servicelocs = {
        instid: list(group) for instid, group in
        itertools.groupby(servicelocs, lambda sloc: sloc.institutionid_id)
        if instid is not None
    }
    for institution in institutions:
        try:
            inst = institution.institutiondetails
        except InstitutionDetails.DoesNotExist:
            continue

        instElement = ElementTree.SubElement(root, "institution")

        if version.is_version_1:
            instCountry = ElementTree.SubElement(instElement, "country")
            instCountry.text = institution.realmid.country.upper()

        if version.ge_version_2:
            instId = ElementTree.SubElement(instElement, "instid")
            instId.text = six.text_type(institution.instid.hex)
            roId = ElementTree.SubElement(instElement, "ROid")
            roId.text = institution.realmid.roid

        instType = ElementTree.SubElement(instElement, "type")
        ertype = institution.ertype
        if version.is_version_1:
            instType.text = six.text_type(ertype)
        else:
            instType.text = get_ertype_string(ertype)

        if version.ge_version_2:
            instStage = ElementTree.SubElement(instElement, "stage")
            instStage.text = six.text_type(institution.stage)

        for realm in institution.instrealm_set.all():
            instRealm = ElementTree.SubElement(instElement, "inst_realm")
            instRealm.text = realm.realm

        for name in inst.institution.inst_name.all():
            name_tag = 'org_name' if version.is_version_1 else 'inst_name'
            instOrgName = ElementTree.SubElement(instElement, name_tag)
            instOrgName.attrib["lang"] = name.lang
            instOrgName.text = u"%s" % name.name

        xml_address_elements(instElement, inst, version=version)

        xml_coordinates_elements(instElement, inst, version=version)

        if version.ge_version_2 and inst.venue_info:
            instVenueInfo = ElementTree.SubElement(instElement, "inst_type")
            instVenueInfo = inst.venue_info

        for contact in inst.contact.all():
            instContact = ElementTree.SubElement(instElement, "contact")

            instContactName = ElementTree.SubElement(instContact, "name")
            instContactName.text = "%s" % (contact.name)

            instContactEmail = ElementTree.SubElement(instContact, "email")
            instContactEmail.text = contact.email

            instContactPhone = ElementTree.SubElement(instContact, "phone")
            instContactPhone.text = contact.phone

            if version.ge_version_2:
                instContactType = ElementTree.SubElement(instContact,
                                                         "type")
                instContactType.text = six.text_type(contact.type)

                instContactPrivacy = ElementTree.SubElement(instContact,
                                                            "privacy")
                instContactPrivacy.text = six.text_type(contact.privacy)

        url_map = {}
        for url in inst.url.all():
            url_map.setdefault(url.urltype, []).append(url)

        for urltype in ('info', 'policy'):
            for url in url_map.get(urltype, []):
                instUrl = ElementTree.SubElement(instElement, "%s_URL" % (url.urltype))
                instUrl.attrib["lang"] = url.lang
                instUrl.text = url.url

        if 'policy' not in url_map:
            instUrl = ElementTree.SubElement(instElement, "policy_URL")
            instUrl.attrib["lang"] = 'en'
            instUrl.text = '-'

        instTs = ElementTree.SubElement(instElement, "ts")
        instTs.text = "%s" % inst.ts.isoformat()
        #Let's go to Institution Service Locations

        for serviceloc in servicelocs[institution.id]:

            instLocation = ElementTree.SubElement(instElement, "location")

            if version.ge_version_2:
                locId = ElementTree.SubElement(instLocation, "locationid")
                locId.text = six.text_type(serviceloc.locationid.hex)

            xml_coordinates_elements(instLocation, serviceloc, version=version)

            if version.ge_version_2:
                locStage = ElementTree.SubElement(instLocation, "stage")
                locStage.text = six.text_type(serviceloc.stage)
                locType = ElementTree.SubElement(instLocation, "type")
                locType.text = six.text_type(serviceloc.geo_type)

            for instlocname in serviceloc.loc_name.all():
                instLocName = ElementTree.SubElement(instLocation, "loc_name")
                instLocName.attrib["lang"] = instlocname.lang
                instLocName.text = instlocname.name

            xml_address_elements(instLocation, serviceloc, version=version)

            if version.ge_version_2 and serviceloc.venue_info:
                instLocVenueInfo = ElementTree.SubElement(
                    instLocation, "location_type")
                instLocVenueInfo = serviceloc.venue_info

            for contact in serviceloc.contact.all():
                instLocContact = ElementTree.SubElement(instLocation, "contact")

                instLocContactName = ElementTree.SubElement(instLocContact, "name")
                instLocContactName.text = "%s" % (contact.name)

                instLocContactEmail = ElementTree.SubElement(instLocContact, "email")
                instLocContactEmail.text = contact.email

                instLocContactPhone = ElementTree.SubElement(instLocContact, "phone")
                instLocContactPhone.text = contact.phone

                if version.ge_version_2:
                    instLocContactType = ElementTree.SubElement(
                        instLocContact, "type")
                    instLocContactType.text = six.text_type(contact.type)

                    instLocContactPrivacy = ElementTree.SubElement(
                        instLocContact, "privacy")
                    instLocContactPrivacy.text = six.text_type(contact.privacy)

            instLocSSID = ElementTree.SubElement(instLocation, "SSID")
            instLocSSID.text = serviceloc.SSID

            # required only under eduroam db v1 schema
            if version.is_version_1 or serviceloc.enc_level:
                instLocEncLevel = ElementTree.SubElement(instLocation,
                                                         "enc_level")
                instLocEncLevel.text = ', '.join(serviceloc.enc_level)

            if version.is_version_1:
                for tag in ['port_restrict', 'transp_proxy', 'IPv6', 'NAT']:
                    tag_set = tag in serviceloc.tag
                    # eduroam db v1 schema caveat: port_restrict not optional
                    if not tag_set and tag != 'port_restrict':
                        continue
                    instLocTagSubElement = ElementTree.SubElement(
                        instLocation, tag)
                    instLocTagSubElement.text = six.text_type(
                        1 if tag_set else 0
                    )

            if serviceloc.AP_no is not None:
                instLocAP_no = ElementTree.SubElement(instLocation, "AP_no")
                instLocAP_no.text = "%s" % int(serviceloc.AP_no)

            if version.is_version_1:
                instLocWired = ElementTree.SubElement(instLocation, "wired")
                instLocWired.text = ("%s" % bool(serviceloc.wired_no)).lower()
            if version.ge_version_2 and serviceloc.wired_no is not None:
                instLocWired_no = ElementTree.SubElement(
                    instLocation, "wired_no")
                instLocWired_no.text = six.text_type(serviceloc.wired_no)

            if version.ge_version_2:
                if serviceloc.tag:
                    instLocTagElement = ElementTree.SubElement(instLocation,
                                                               'tag')
                    instLocTagElement.text = ','.join(serviceloc.tag)

                instLocAvailElement = ElementTree.SubElement(
                    instLocation, 'availability')
                instLocAvailElement.text = six.text_type(
                    serviceloc.physical_avail)

                if serviceloc.operation_hours:
                    instLocOperHoursElement = ElementTree.SubElement(
                        instLocation, 'operation_hours')
                    instLocOperHoursElement.text = \
                        serviceloc.operation_hours

            for url in serviceloc.url.all():
                instLocUrl = ElementTree.SubElement(
                    instLocation,
                    "%s_URL" % (url.urltype)
                )
                instLocUrl.attrib["lang"] = url.lang
                instLocUrl.text = url.url

    return render(
        request,
        "general/institution.xml",
        context={
            "xml": to_xml(root)
        },
        content_type="application/xml"
    )


@never_cache
@detect_eduroam_db_version
def realmxml(request, version):
    realm = Realm.objects.all()[0]
    ElementTree._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ElementTree.Element("realms" if version.is_version_1 else "ROs")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "noNamespaceSchemaLocation", "realm.xsd" if version.is_version_1 else "ro.xsd")
    realmElement = ElementTree.SubElement(root, "realm" if version.is_version_1 else "RO")

    if version.ge_version_2:
        realmROid = ElementTree.SubElement(realmElement, "ROid")
        realmROid.text = realm.roid

    realmCountry = ElementTree.SubElement(realmElement, "country")
    realmCountry.text = realm.country.upper()

    if version.is_version_1:
        realmStype = ElementTree.SubElement(realmElement, "stype")
        realmStype.text = "%s" % realm.stype

    if version.ge_version_2:
        realmStage = ElementTree.SubElement(realmElement, "stage")
        realmStage.text = six.text_type(realm.stage)

    for name in realm.org_name.all():
        realmOrgName = ElementTree.SubElement(realmElement, "org_name")
        realmOrgName.attrib["lang"] = name.lang
        realmOrgName.text = u"%s" % name.name

    xml_address_elements(realmElement, realm, version=version)

    xml_coordinates_elements(realmElement, realm, version=version)

    for contact in realm.contact.all():
        realmContact = ElementTree.SubElement(realmElement, "contact")

        realmContactName = ElementTree.SubElement(realmContact, "name")
        realmContactName.text = "%s" % (contact.name)

        realmContactEmail = ElementTree.SubElement(realmContact, "email")
        realmContactEmail.text = contact.email

        realmContactPhone = ElementTree.SubElement(realmContact, "phone")
        realmContactPhone.text = contact.phone

        if version.ge_version_2:
            realmContactType = ElementTree.SubElement(realmContact,
                                                      "type")
            realmContactType.text = six.text_type(contact.type)

            realmContactPrivacy = ElementTree.SubElement(realmContact,
                                                         "privacy")
            realmContactPrivacy.text = six.text_type(contact.privacy)

    url_map = {}
    for url in realm.url.all():
        url_map.setdefault(url.urltype, []).append(url)

    for urltype in ('info', 'policy'):
        for url in url_map.get(urltype, []):
            realmUrl = ElementTree.SubElement(realmElement, "%s_URL" % (url.urltype))
            realmUrl.attrib["lang"] = url.lang
            realmUrl.text = url.url

    instTs = ElementTree.SubElement(realmElement, "ts")
    instTs.text = "%s" % realm.ts.isoformat()

    return render(
        request,
        "general/realm.xml",
        context={"xml": to_xml(root)},
        content_type="application/xml"
    )


@never_cache
def realmdataxml(request):
    realm = Realm.objects.all()[0]
    ElementTree._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ElementTree.Element("realm_data_root")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "noNamespaceSchemaLocation", "realm_data.xsd")

    realmdataElement = ElementTree.SubElement(root, "realm_data")

    realmCountry = ElementTree.SubElement(realmdataElement, "country")
    realmCountry.text = realm.country.upper()

    nIdpCountry = ElementTree.SubElement(realmdataElement, "number_IdP")
    nIdpCountry.text = "%s" % len(realm.institution_set.filter(ertype=ERTYPES.IDP))

    nSPCountry = ElementTree.SubElement(realmdataElement, "number_SP")
    nSPCountry.text = "%s" % len(realm.institution_set.filter(ertype=ERTYPES.SP))

    nSPIdpCountry = ElementTree.SubElement(realmdataElement, "number_SPIdP")
    nSPIdpCountry.text = "%s" % len(realm.institution_set.filter(ertype=ERTYPES.IDPSP))

    ninstCountry = ElementTree.SubElement(realmdataElement, "number_inst")
    ninstCountry.text = "%s" % len(realm.institution_set.all())

    nuserCountry = ElementTree.SubElement(realmdataElement, "number_user")
    insts = realm.institution_set.all()
    users = 0
    for inst in insts:
        try:
            if inst.institutiondetails.number_user:
                users = users + inst.institutiondetails.number_user
        except InstitutionDetails.DoesNotExist:
            pass
    nuserCountry.text = "%s" % users

    nIdCountry = ElementTree.SubElement(realmdataElement, "number_id")
    insts = realm.institution_set.all()
    ids = 0
    for inst in insts:
        try:
            if inst.institutiondetails.number_id:
                ids = ids + inst.institutiondetails.number_id
        except InstitutionDetails.DoesNotExist:
            pass
    nIdCountry.text = "%s" % ids

    # Get the latest ts from all tables...
    datetimes = []
    if InstitutionDetails.objects.aggregate(Max('ts'))['ts__max']:
        datetimes.append(InstitutionDetails.objects.aggregate(Max('ts'))['ts__max'])
    if Realm.objects.aggregate(Max('ts'))['ts__max']:
        datetimes.append(Realm.objects.aggregate(Max('ts'))['ts__max'])
    if InstServer.objects.aggregate(Max('ts'))['ts__max']:
        datetimes.append(InstServer.objects.aggregate(Max('ts'))['ts__max'])
    if ServiceLoc.objects.aggregate(Max('ts'))['ts__max']:
        datetimes.append(ServiceLoc.objects.aggregate(Max('ts'))['ts__max'])
    if len(datetimes) == 0:
        datetimes.append(datetime.datetime.now())
    instTs = ElementTree.SubElement(realmdataElement, "ts")
    instTs.text = "%s" % max(datetimes).isoformat()
    return render(
        request,
        "general/realm_data.xml",
        context={"xml": to_xml(root)},
        content_type="application/xml"
    )


@never_cache
def servdata(request):
    root = {}
    hosts = InstServer.objects.all()
    insts = Institution.objects.all()

    clients = hosts.filter(ertype__in=ERTYPE_ROLES.SP)
    if clients:
        root['clients'] = {}
    for srv in clients:
        srv_id = getSrvIdentifier(srv, "client_")
        srv_dict = {}
        srv_dict['host'] = srv.host
        if srv.name:
            srv_dict['label'] = srv.name
        srv_dict['secret'] = srv.secret
        root['clients'].update({srv_id: srv_dict})

    servers = hosts.filter(ertype__in=ERTYPE_ROLES.IDP)
    if servers:
        root['servers'] = {}
    for srv in servers:
        srv_id = getSrvIdentifier(srv, "server_")
        srv_dict = {}
        srv_dict['rad_pkt_type'] = srv.rad_pkt_type
        if srv.rad_pkt_type.find("auth") != -1:
            srv_dict['auth_port'] = srv.auth_port
        if srv.rad_pkt_type.find("acct") != -1:
            srv_dict['acct_port'] = srv.acct_port
        srv_dict['host'] = srv.host
        if srv.name:
            srv_dict['label'] = srv.name
        srv_dict['secret'] = srv.secret
        srv_dict['status_server'] = bool(srv.status_server)
        root['servers'].update({srv_id: srv_dict})

    if insts:
        root['institutions'] = []
    for inst in insts:
        inst_dict = {}
        if not hasattr(inst, "institutiondetails"):
            continue
        if hasattr(inst.institutiondetails, "oper_name") and \
                inst.institutiondetails.oper_name:
            inst_dict['id'] = inst.institutiondetails.oper_name
        inst_dict['type'] = inst.ertype
        if inst.ertype in ERTYPE_ROLES.SP:
            inst_clients = inst.servers.filter(ertype__in=ERTYPE_ROLES.SP)
            if inst_clients:
                inst_dict['clients'] = [getSrvIdentifier(srv, "client_") for
                                        srv in inst_clients]
        if inst.ertype in ERTYPE_ROLES.IDP:
            inst_realms = inst.instrealm_set.all()
            if inst_realms:
                inst_dict['realms'] = {}
            for realm in inst_realms:
                rdict = {}
                rdict[realm.realm] = {}
                rdict[realm.realm]['proxy_to'] = [getSrvIdentifier(proxy, "server_") for
                                                  proxy in realm.proxyto.all()]
                inst_dict['realms'].update(rdict)
        root['institutions'].append(inst_dict)

    if 'HTTP_ACCEPT' in request.META:
        if request.META.get('HTTP_ACCEPT') == "application/json":
            resp_content_type = "application/json"
            resp_body = json.dumps(root)
        elif request.META.get('HTTP_ACCEPT') in [
            "text/yaml",
            "text/x-yaml",
            "application/yaml",
            "application/x-yaml"
        ]:
            resp_content_type = request.META.get('HTTP_ACCEPT')
    try:
        resp_content_type
    except NameError:
        resp_content_type = "text/yaml"

    if resp_content_type.find("yaml") != -1:
        from yaml import dump
        try:
            from yaml import CSafeDumper as SafeDumper
        except ImportError:
            from yaml import SafeDumper
        resp_body = dump(root,
                         Dumper=SafeDumper,
                         allow_unicode=True,
                         default_flow_style=False)
        resp_content_type += "; charset=utf-8"

    return HttpResponse(resp_body,
                        content_type=resp_content_type)


@never_cache
def adminlist(request):
    users = User.objects.filter(userprofile__isnull=False,
                                registrationprofile__isnull=False)
    data = [
        (u.userprofile.institution.get_name(request.LANGUAGE_CODE),
         u.first_name + " " + u.last_name,
         m)
        for u in users if
        u.registrationprofile.activation_key == "ALREADY_ACTIVATED"
        for m in u.email.split(';')
    ]
    with setlocale((request.LANGUAGE_CODE, 'UTF-8'), locale.LC_COLLATE):
        data.sort(key=lambda d: compat_strxfrm(d[0]))
    resp_body = ""
    for (foreas, onoma, email) in data:
        resp_body += u'{email}\t{onoma}'.format(
            email=email,
            onoma=onoma
        ) + "\n"
    return HttpResponse(resp_body,
                        content_type="text/plain; charset=utf-8")


def _cat_api_cache_action(request, cat_instance):
    if cat_instance is None:
        cat_instance = 'production'
    action = request.GET.get('action', None)
    if not action:
        return None
    # by default we only cache large/expensive API calls for 10 mins
    timeouts_default = {
        'listAllIdentityProviders': 600,
        'listIdentityProviders':    600,
        'orderIdentityProviders':   600,
        'listCountries':            600,
        'sendLogo':                 600,
        'detectOS':                 600,
        }
    timeouts_settings = getattr(settings, 'CAT_USER_API_CACHE_TIMEOUT', {})
    timeouts = timeouts_settings.get(cat_instance, timeouts_default)
    try:
        timeout = timeouts[action]
    # no-cache if action not found in timeout settings
    except KeyError:
        return None
    cache_kwargs = {}
    # no cache key prefix by default
    cache_prefix = settings_dict_get('CAT_USER_API_PROXY_OPTIONS',
                                     cat_instance, 'cache_prefix',
                                     default='')
    if cache_prefix:
        cache_kwargs['key_prefix'] = cache_prefix
    # cache alias: True means use default, None means no-cache
    cache_alias = settings_dict_get('CAT_USER_API_PROXY_OPTIONS',
                                    cat_instance, 'cache',
                                    default=True)
    if cache_alias is None:
        return None
    if cache_alias is not True:
        cache_kwargs['cache'] = cache_alias
    return (timeout, cache_kwargs)

@cache_page_ifreq(_cat_api_cache_action)
@dont_vary_on('Cookie')
def cat_user_api_proxy(request, cat_instance):
    if cat_instance is None:
        cat_instance = 'production'
    cat_instance_name = cat_instance
    cat_instance = settings_dict_get('CAT_AUTH', cat_instance)
    if cat_instance is None:
        return HttpResponseNotFound('<h1>CAT instance not found</h1>')
    cat_api_url = cat_instance.get('CAT_USER_API_URL', None)
    if cat_api_url is None:
        return HttpResponseNotFound('<h1>CAT user API URL not found</h1>')
    if request.method != 'GET':
        return HttpResponseBadRequest('<h1>Only GET requests are allowed</h1>')
    qs = request.META['QUERY_STRING']
    qs = '?%s' % qs if qs else ''
    cat_api_url += qs
    cat_api_action = request.GET.get('action', None)
    if not cat_api_action:
        return HttpResponseBadRequest('<h1>Invalid or no action specified</h1>')
    if cat_api_action == 'downloadInstaller' and \
      settings_dict_get('CAT_USER_API_PROXY_OPTIONS',
                        cat_instance_name, 'redirect_downloads',
                        default=True):
        return HttpResponseRedirect(cat_api_url)
    headers = {
        'X-Forwarded-For': request.META['REMOTE_ADDR'],
        'X-Forwarded-Host': request.META['HTTP_HOST'],
        'X-Forwarded-Server': request.META['SERVER_NAME']
        }
    for h in ['CONTENT_TYPE', 'HTTP_ACCEPT', 'HTTP_X_REQUESTED_WITH',
              'HTTP_REFERER', 'HTTP_USER_AGENT']:
        if h in request.META:
            hh = h.replace('HTTP_', '') if h.startswith('HTTP_') else h
            hh = '-'.join([w.capitalize() for w in hh.split('_')])
            headers[hh] = request.META[h]
    r = requests.get(cat_api_url, headers=headers)
    cc = r.headers.get('cache-control', '')
    ct = r.headers.get('content-type', 'text/plain')
    try:
        cl = int(r.headers['content-length'])
    except (KeyError, ValueError):
        cl = len(r.content)
    cd = r.headers.get('content-disposition', None)
    if ct.startswith('text/html') and cl > 0 and r.content[0] in ['{', '[']:
        ct = ct.replace('text/html', 'application/json')
    resp = HttpResponse(r.content, content_type=ct)
    resp.status_code = r.status_code
    resp.reason_phrase = r.reason
    allow_cors = settings_dict_get('CAT_USER_API_PROXY_OPTIONS',
                                   cat_instance_name, 'allow_cross_origin',
                                   default=False)
    if allow_cors:
        origin = '*'
        if allow_cors is 'origin' and 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
            patch_vary_headers(resp, ['Origin'])
        resp.setdefault('Access-Control-Allow-Origin', origin)
        resp.setdefault('Access-Control-Allow-Method', 'GET')
    if cat_api_action == 'detectOS':
        patch_vary_headers(resp, ['User-Agent'])
    if cd is not None:
        resp.setdefault('Content-Disposition', cd)
    resp.setdefault('Cache-Control', cc)
    max_age = get_max_age(resp) or 0
    del resp['Cache-Control']
    if max_age > 0:
        patch_response_headers(resp, max_age)
    return resp
    
def to_xml(ele, encoding="UTF-8"):
    '''
    Convert and return the XML for an *ele*
    (:class:`~xml.etree.ElementTree.Element`)
    with specified *encoding*.'''
    # on python3, we need to get a string, not bytestring - so if requesting unicode, request it as "unicode"
    xml = ElementTree.tostring(ele, "unicode" if six.PY3 and encoding.lower()=="utf-8" else encoding)
    return xml if xml.startswith('<?xml') else '<?xml version="1.0" encoding="%s"?>%s' % (encoding, xml)


def getSrvIdentifier(srv, prefix):
    if not hasattr(srv, "id"):
        return None
    retid = "{0}{1:d}".format(prefix,
                              srv.id)
    if hasattr(srv, "name") and srv.name:
        from django.template.defaultfilters import slugify
        retid = "{0}_{1}".format(retid,
                                 slugify(srv.name))
    return retid


def getInstContacts(inst):
    contacts = InstitutionContactPool.objects.filter(institution=inst)
    contact_pks = []
    for contact in contacts:
        contact_pks.append(contact.contact.pk)
    return list(set(contact_pks))


def getInstServers(inst, idpsp=False):
    servers = InstServer.objects.filter(instid=inst)
    if idpsp:
        servers = servers.filter(ertype__in=ERTYPE_ROLES.IDP)
    server_pks = []
    for server in servers:
        server_pks.append(server.pk)
    return list(set(server_pks))


def rad(x):
    return x * math.pi / 180


def send_new_mail(subject, message, from_email, recipient_list, bcc_list):
    return EmailMessage(
        subject,
        message,
        from_email,
        recipient_list,
        bcc_list
    ).send()


def lookupShibAttr(attrmap, requestMeta):
    for attr in attrmap:
        if (attr in requestMeta.keys()):
            if len(requestMeta[attr]) > 0:
                return requestMeta[attr]
    return ''

# def get_i18n_name(i18n_name, lang, default_lang='en', default_name='unknown'):
#     names = i18n_name.filter(lang=lang)
#     if names.count()==0:
#         names = i18n_name.filter(lang=default_lang)
#     if names.count()==0:
#         return default_name
#     else:
#         # follow ServiceLoc.get_name()
#         return ', '.join([i.name for i in names])

def get_nro_name(lang):
    return Realm.objects.\
        get(country=settings.NRO_COUNTRY_CODE).\
        get_name(lang=lang)

def settings_dict_get(setting, *keys, **opts):
    dct = getattr(settings, setting, {})
    for k in keys:
        dct = dct.get(k, {})
    if dct == {}:
        dct = opts.get('default', None)
    return dct

# utility function to merge two dictionaries
def merge_dicts(dict1, dict2):
    return dict(itertools.chain(dict1.items(), dict2.items()))
