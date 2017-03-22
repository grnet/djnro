# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import json
import bz2
import math
import datetime
from xml.etree import ElementTree
import locale
from localectxmgr import setlocale
import requests

from django.shortcuts import render_to_response, redirect, render
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    HttpResponseBadRequest
)
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
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
from django.contrib.auth import authenticate, login
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
)
from accounts.models import UserProfile
from edumanage.forms import (
    InstDetailsForm,
    UrlFormSetFactInst,
    InstRealmForm,
    UserProfileForm,
    ContactForm,
    MonLocalAuthnParamForm,
    InstRealmMonForm,
    ServiceLocForm,
    NameFormSetFact,
    UrlFormSetFact,
    InstServerForm
)
from registration.models import RegistrationProfile
from edumanage.decorators import (social_active_required,
                                  cache_page_ifreq)
from django.utils.cache import (
    patch_vary_headers
)
from django_dont_vary_on.decorators import dont_vary_on
from utils.cat_helper import CatQuery


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
        return render_to_response(
            'edumanage/welcome_manage.html',
            context_instance=RequestContext(request, base_response(request))
        )
    except AttributeError:
        return render(
            request,
            'edumanage/welcome_manage.html',
            {}
        )
    if user.is_authenticated() and user.is_active and profile.is_social_active:
        return redirect(reverse('manage'))
    else:
        return render(
            request,
            'edumanage/welcome_manage.html',
            {}
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
        return render_to_response(
            'edumanage/welcome.html',
            context_instance=RequestContext(request, base_response(request))
        )
    services = ServiceLoc.objects.filter(institutionid=inst)
    services_list.extend([s for s in services])
    servers = InstServer.objects.filter(instid=inst)
    servers_list.extend([s for s in servers])
    return render_to_response(
        'edumanage/welcome.html',
        {
            'institution': inst,
            'services': services_list,
            'servers': servers_list,
        },
        context_instance=RequestContext(request, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def institutions(request):
    user = request.user
    dict = {}
    try:
        profile = user.userprofile
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    dict['institution'] = inst.pk
    form = InstDetailsForm(initial=dict)
    form.fields['institution'].widget.attrs['readonly'] = True
    return render_to_response(
        'edumanage/institution.html',
        {
            'institution': inst,
            'form': form,
        },
        context_instance=RequestContext(request, base_response(request))
    )


@login_required
@social_active_required
@never_cache
def add_institution_details(request, institution_pk):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))

    if institution_pk and int(inst.pk) != int(institution_pk):
        messages.add_message(
            request,
            messages.ERROR,
            'You have no rights on this Institution'
        )
        return HttpResponseRedirect(reverse("institutions"))

    if request.method == "GET":
        try:
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(instance=inst_details)
            UrlFormSet = generic_inlineformset_factory(
                URL_i18n,
                extra=2,
                formset=UrlFormSetFactInst,
                can_delete=True
            )
            urls_form = UrlFormSet(prefix='urlsform', instance=inst_details)
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm()
            form.fields['institution'] = forms.ModelChoiceField(
                queryset=Institution.objects.filter(pk=institution_pk),
                empty_label=None
            )
            UrlFormSet = generic_inlineformset_factory(
                URL_i18n,
                extra=2,
                can_delete=True
            )
            urls_form = UrlFormSet(prefix='urlsform')

        form.fields['contact'] = forms.ModelMultipleChoiceField(
            queryset=Contact.objects.filter(pk__in=getInstContacts(inst))
        )
        return render_to_response(
            'edumanage/institution_edit.html',
            {'institution': inst, 'form': form, 'urls_form': urls_form},
            context_instance=RequestContext(request, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFactInst, can_delete=True)
        try:
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(request_data, instance=inst_details)
            urls_form = UrlFormSet(request_data, instance=inst_details, prefix='urlsform')
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm(request_data)
            urls_form = UrlFormSet(request_data, prefix='urlsform')
        UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFactInst, can_delete=True)
        if form.is_valid() and urls_form.is_valid():
            instdets = form.save()
            urls_form.instance = instdets
            urls_form.save()
            return HttpResponseRedirect(reverse("institutions"))
        else:
            form.fields['institution'] = forms.ModelChoiceField(
                queryset=Institution.objects.filter(pk=institution_pk),
                empty_label=None
            )
            form.fields['contact'] = forms.ModelMultipleChoiceField(
                queryset=Contact.objects.filter(pk__in=getInstContacts(inst))
            )
            return render_to_response(
                'edumanage/institution_edit.html',
                {'institution': inst, 'form': form, 'urls_form': urls_form},
                context_instance=RequestContext(
                    request, base_response(request)
                )
            )


@login_required
@social_active_required
@never_cache
def services(request, service_pk):
    user = request.user
    try:
        profile = user.userprofile
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [2, 3]:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Location. Your institution should be either SP or IdP/SP'
        )
        return render_to_response(
            'edumanage/services.html',
            {'institution': inst},
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/service_details.html',
            {
                'institution': inst,
                'service': services,
            },
            context_instance=RequestContext(request, base_response(request))
        )

    return render_to_response(
        'edumanage/services.html',
        {
            'institution': inst,
            'services': services,
        },
        context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [2, 3]:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Service. Your institution should be either SP or IdP/SP'
        )
        return render_to_response(
            'edumanage/services_edit.html',
            {'edit': edit},
            context_instance=RequestContext(request, base_response(request))
        )
    if request.method == "GET":

        # Determine add or edit
        try:
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(instance=service)
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm()
            if service_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this location'
                )
                return HttpResponseRedirect(reverse("services"))
        form.fields['institutionid'] = forms.ModelChoiceField(
            queryset=Institution.objects.filter(pk=inst.pk),
            empty_label=None
        )
        UrlFormSet = generic_inlineformset_factory(
            URL_i18n,
            extra=2,
            can_delete=True
        )
        NameFormSet = generic_inlineformset_factory(
            Name_i18n,
            extra=2,
            can_delete=True
        )
        urls_form = UrlFormSet(prefix='urlsform')
        names_form = NameFormSet(prefix='namesform')
        if (service):
            NameFormSet = generic_inlineformset_factory(
                Name_i18n,
                extra=1,
                formset=NameFormSetFact, can_delete=True
            )
            names_form = NameFormSet(instance=service, prefix='namesform')
            UrlFormSet = generic_inlineformset_factory(
                URL_i18n,
                extra=2,
                formset=UrlFormSetFact,
                can_delete=True
            )
            urls_form = UrlFormSet(instance=service, prefix='urlsform')
        form.fields['contact'] = forms.ModelMultipleChoiceField(
            queryset=Contact.objects.filter(pk__in=getInstContacts(inst))
        )
        if service:
            edit = True
        for url_form in urls_form.forms:
            url_form.fields['urltype'] = forms.ChoiceField(
                choices=(('', '----------'), ('info', 'Info'),)
            )
        return render_to_response(
            'edumanage/services_edit.html',
            {
                'form': form,
                'services_form': names_form,
                'urls_form': urls_form,
                "edit": edit
            },
            context_instance=RequestContext(request, base_response(request))
        )
    elif request.method == 'POST':
        request_data = request.POST.copy()
        NameFormSet = generic_inlineformset_factory(
            Name_i18n,
            extra=1,
            formset=NameFormSetFact,
            can_delete=True
        )
        UrlFormSet = generic_inlineformset_factory(
            URL_i18n,
            extra=2,
            formset=UrlFormSetFact,
            can_delete=True
        )
        try:
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(request_data, instance=service)
            names_form = NameFormSet(
                request_data,
                instance=service,
                prefix='namesform'
            )
            urls_form = UrlFormSet(
                request_data,
                instance=service,
                prefix='urlsform'
            )
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm(request_data)
            names_form = NameFormSet(request_data, prefix='namesform')
            urls_form = UrlFormSet(request_data, prefix='urlsform')
            if service_pk:
                messages.add_message(
                    request,
                    messages.ERROR,
                    'You have no rights to edit this location'
                )
                return HttpResponseRedirect(reverse("services"))
        if form.is_valid() and names_form.is_valid() and urls_form.is_valid():
            serviceloc = form.save()
            service = serviceloc
            names_form.instance = service
            urls_form.instance = service
            names_form.save()
            urls_form.save()
            return HttpResponseRedirect(reverse("services"))
        else:
            form.fields['institutionid'] = forms.ModelChoiceField(
                queryset=Institution.objects.filter(pk=inst.pk),
                empty_label=None
            )
            form.fields['contact'] = forms.ModelMultipleChoiceField(
                queryset=Contact.objects.filter(pk__in=getInstContacts(inst))
            )
        if service:
            edit = True
        for url_form in urls_form.forms:
            url_form.fields['urltype'] = forms.ChoiceField(
                choices=(('', '----------'), ('info', 'Info'),)
            )
        return render_to_response(
            'edumanage/services_edit.html',
            {
                'institution': inst,
                'form': form,
                'services_form': names_form,
                'urls_form': urls_form,
                'edit': edit
            },
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/server_details.html',
            {
                'institution': inst,
                'server': servers,
            },
            context_instance=RequestContext(request, base_response(request))
        )
    return render_to_response(
        'edumanage/servers.html',
        {
            'servers': servers
        },
        context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
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

        return render_to_response(
            'edumanage/servers_edit.html',
            {
                'form': form,
                'edit': edit
            },
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/servers_edit.html',
            {
                'institution': inst,
                'form': form,
                'edit': edit
            },
            context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [1, 3]:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Enrollments. Your institution should be either IdP or IdP/SP'
        )
        return render_to_response(
            'edumanage/catenroll.html',
            {'status': False},
            context_instance=RequestContext(request, base_response(request))
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
            return render_to_response(
                'edumanage/catenroll.html',
                {'status': False},
                context_instance=RequestContext(request, base_response(request))
            )
        return render_to_response(
            'edumanage/catenroll.html',
            {
                'status': True,
                'current_enrollments': current_enrollments,
                'cat_instances': available_enrollments
            },
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/catenroll.html',
            {
                'status': True,
                'response_status': status,
                'response': response,
                'cat_url': cat_url,
                'inst_uid': inst_uid
            },
            context_instance=RequestContext(request, base_response(request))
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
    if inst.ertype not in [1, 3]:
        messages.add_message(
            request,
            messages.ERROR,
            'Cannot add/edit Realms. Your institution should be either IdP or IdP/SP'
        )
    return render_to_response(
        'edumanage/realms.html',
        {'realms': realms},
        context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [1, 3]:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Realm. Your institution should be either IdP or IdP/SP')
        return render_to_response(
            'edumanage/realms_edit.html',
            {'edit': edit},
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/realms_edit.html',
            {'form': form, 'edit': edit},
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/realms_edit.html',
            {'institution': inst, 'form': form, 'edit': edit},
            context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
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
    return render_to_response(
        'edumanage/contacts.html',
        {'contacts': contacts},
        context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
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
        return render_to_response(
            'edumanage/contacts_edit.html',
            {
                'form': form,
                'edit': edit
            },
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/contacts_edit.html',
            {'form': form, "edit": edit},
            context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        instrealmmons = InstRealmMon.objects.filter(realm__instid=inst)
    return render_to_response(
        'edumanage/instrealmmons.html',
        {'realms': instrealmmons},
        context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
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
        return render_to_response(
            'edumanage/instrealmmon_edit.html',
            {'form': form, 'edit': edit},
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/instrealmmon_edit.html',
            {'form': form, "edit": edit},
            context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
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
        return render_to_response(
            'edumanage/monlocauthpar_edit.html',
            {'form': form,"edit" : edit, "realm":instrealmmon},
            context_instance=RequestContext(request, base_response(request))
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
        return render_to_response(
            'edumanage/monlocauthpar_edit.html',
            {'form': form, "edit": edit, "realm":instrealmmon},
            context_instance=RequestContext(request, base_response(request))
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
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))

    if request.method == "GET":
        form = ContactForm()
        return render_to_response(
            'edumanage/add_user.html',
            {'form': form},
            context_instance=RequestContext(request, base_response(request))
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
            return render_to_response(
                'edumanage/add_user.html',
                {'form': form},
                context_instance=RequestContext(
                    request,
                    base_response(request)
                )
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
        institution_canhaveservicelocs = institution.ertype in [2, 3]
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
        servicelocs = ServiceLoc.objects.filter(institutionid=inst)

        locs = []
        for sl in servicelocs:
            response_location = {}
            response_location['lat'] = u"%s" % sl.latitude
            response_location['lng'] = u"%s" % sl.longitude
            response_location['address'] = u"%s<br>%s" % (
                sl.address_street,
                sl.address_city
            )
            if len(sl.enc_level[0]) != 0:
                response_location['enc'] = u"%s" % (','.join(sl.enc_level))
            else:
                response_location['enc'] = u"-"
            response_location['AP_no'] = u"%s" % (sl.AP_no)
            response_location['name'] = get_i18n_name(sl.loc_name, lang, 'en', 'unknown')
            response_location['port_restrict'] = u"%s" % (sl.port_restrict)
            response_location['transp_proxy'] = u"%s" % (sl.transp_proxy)
            response_location['IPv6'] = u"%s" % (sl.IPv6)
            response_location['NAT'] = u"%s" % (sl.NAT)
            response_location['wired'] = u"%s" % (sl.wired)
            response_location['SSID'] = u"%s" % (sl.SSID)
            response_location['key'] = u"%s" % sl.pk
            locs.append(response_location)
        return HttpResponse(json.dumps(locs), content_type='application/json')
    else:
        return HttpResponseNotFound('<h1>Something went really wrong</h1>')


@login_required
@never_cache
def overview(request):
    user = request.user
    if user.has_perm('accounts.overview'):
        users = User.objects.all()
        institutions = Institution.objects.all()
        return render_to_response(
            'overview/index.html',
            {'users': users, 'institutions': institutions},
            context_instance=RequestContext(request)
        )
    else:
        return render_to_response(
            'overview/index.html',
            {'violation': True},
            context_instance=RequestContext(request)
        )


@never_cache
def get_all_services(request):
    lang = request.LANGUAGE_CODE
    servicelocs = ServiceLoc.objects.all()
    locs = []
    for sl in servicelocs:
        response_location = {}
        response_location['lat'] = u"%s" % sl.latitude
        response_location['lng'] = u"%s" % sl.longitude
        response_location['address'] = u"%s<br>%s" % (
            sl.address_street, sl.address_city
        )
        if len(sl.enc_level[0]) != 0:
            response_location['enc'] = u"%s" % (
                ','.join(sl.enc_level)
            )
        else:
            response_location['enc'] = u"-"
        response_location['AP_no'] = u"%s" % (sl.AP_no)
        response_location['inst'] = get_i18n_name(sl.institutionid.org_name, lang, 'en', 'unknown')
        response_location['name'] = get_i18n_name(sl.loc_name, lang, 'en', 'unknown')
        response_location['port_restrict'] = u"%s" % (sl.port_restrict)
        response_location['transp_proxy'] = u"%s" % (sl.transp_proxy)
        response_location['IPv6'] = u"%s" % (sl.IPv6)
        response_location['NAT'] = u"%s" % (sl.NAT)
        response_location['wired'] = u"%s" % (sl.wired)
        response_location['SSID'] = u"%s" % (sl.SSID)
        response_location['key'] = u"%s" % sl.pk
        locs.append(response_location)
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
            return render_to_response(
                'status.html',
                {'error': error, "missing_attributes": True},
                context_instance=RequestContext(request)
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
                return render_to_response(
                    'registration/select_institution.html',
                    {'form': form},
                    context_instance=RequestContext(request)
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

                return render_to_response(
                    'status.html',
                    {'status': status, 'inactive': True},
                    context_instance=RequestContext(request)
                )
        else:
            error = _(
                "Something went wrong during user authentication."
                " Contact your administrator %s" % user
            )
            return render_to_response(
                'status.html',
                {'error': error},
                context_instance=RequestContext(request)
            )
    except Exception as e:
        error = _("Invalid login procedure. Error: %s" % e)
        return render_to_response(
            'status.html',
            {'error': error},
            context_instance=RequestContext(request)
        )


@never_cache
def geolocate(request):
    return render_to_response(
        'front/geolocate.html',
        context_instance=RequestContext(request)
    )


@never_cache
def api(request):
    current_site = get_current_site(request)
    return render_to_response(
        'front/api.html',
        {'site': current_site},
        context_instance=RequestContext(request)
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
        dets.sort(cmp=locale.strcoll,
                  key=lambda x: unicode(x.institution.
                                        get_name(lang=request.LANGUAGE_CODE)))
    return render_to_response(
        'front/participants.html',
        {
            'institutions': dets,
            'catexists': cat_exists
        },
        context_instance=RequestContext(request)
    )


@never_cache
def connect(request):
    institutions = Institution.objects.filter(ertype__in=[1,3],
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
        dets.sort(cmp=locale.strcoll,
                  key=lambda x: unicode(x.institution.
                                        get_name(lang=request.LANGUAGE_CODE)))
    return render_to_response(
        'front/connect.html',
        {
            'institutions': dets,
            'institutions_cat': dets_cat,
            'catexists': cat_exists
        },
        context_instance=RequestContext(request)
    )


@never_cache
def selectinst(request):
    if request.method == 'POST':
        request_data = request.POST.copy()
        user = request_data['user']
        try:
            UserProfile.objects.get(user=user)
            error = _("Violation warning: User account is already associated with an institution.The event has been logged and our administrators will be notified about it")
            return render_to_response(
                'status.html',
                {'error': error, 'inactive': True},
                context_instance=RequestContext(request)
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
            return render_to_response(
                'status.html',
                {'status': error, 'inactive': True},
                context_instance=RequestContext(request)
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
            return render_to_response(
                'registration/select_institution.html',
                {'form': form, 'nomail': nomail},
                context_instance=RequestContext(request)
            )


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
        return render_to_response(
            'front/world.html',
            context_instance=RequestContext(request)
        )


@never_cache
def managementPage(request):
    return render_to_response(
        'front/management.html',
        context_instance=RequestContext(request)
    )


def getPoints():
    points = cache.get('points')
    if points:
        points = bz2.decompress(points)
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
        cache.set('points', bz2.compress(points), 60 * 3600 * 24)
        return json.loads(points)


@never_cache
def instxml(request):
    ElementTree._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ElementTree.Element("institutions")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "noNamespaceSchemaLocation", "institution.xsd")
    institutions = Institution.objects.all()
    for institution in institutions:
        try:
            inst = institution.institutiondetails
            if not inst:
                continue
        except InstitutionDetails.DoesNotExist:
            continue

        instElement = ElementTree.SubElement(root, "institution")

        instCountry = ElementTree.SubElement(instElement, "country")
        instCountry.text = ("%s" % inst.institution.realmid.country).upper()

        instType = ElementTree.SubElement(instElement, "type")
        instType.text = "%s" % inst.institution.ertype

        for realm in institution.instrealm_set.all():
            instRealm = ElementTree.SubElement(instElement, "inst_realm")
            instRealm.text = realm.realm

        for name in inst.institution.org_name.all():
            instOrgName = ElementTree.SubElement(instElement, "org_name")
            instOrgName.attrib["lang"] = name.lang
            instOrgName.text = u"%s" % name.name

        instAddress = ElementTree.SubElement(instElement, "address")

        instAddrStreet = ElementTree.SubElement(instAddress, "street")
        instAddrStreet.text = inst.address_street

        instAddrCity = ElementTree.SubElement(instAddress, "city")
        instAddrCity.text = inst.address_city

        for contact in inst.contact.all():
            instContact = ElementTree.SubElement(instElement, "contact")

            instContactName = ElementTree.SubElement(instContact, "name")
            instContactName.text = "%s" % (contact.name)

            instContactEmail = ElementTree.SubElement(instContact, "email")
            instContactEmail.text = contact.email

            instContactPhone = ElementTree.SubElement(instContact, "phone")
            instContactPhone.text = contact.phone

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

        for serviceloc in inst.institution.serviceloc_set.all():
            instLocation = ElementTree.SubElement(instElement, "location")

            instLong = ElementTree.SubElement(instLocation, "longitude")
            instLong.text = "%s" % serviceloc.longitude

            instLat = ElementTree.SubElement(instLocation, "latitude")
            instLat.text = "%s" % serviceloc.latitude

            for instlocname in serviceloc.loc_name.all():
                instLocName = ElementTree.SubElement(instLocation, "loc_name")
                instLocName.attrib["lang"] = instlocname.lang
                instLocName.text = instlocname.name

            instLocAddress = ElementTree.SubElement(instLocation, "address")

            instLocAddrStreet = ElementTree.SubElement(instLocAddress, "street")
            instLocAddrStreet.text = serviceloc.address_street

            instLocAddrCity = ElementTree.SubElement(instLocAddress, "city")
            instLocAddrCity.text = serviceloc.address_city

            for contact in serviceloc.contact.all():
                instLocContact = ElementTree.SubElement(instLocation, "contact")

                instLocContactName = ElementTree.SubElement(instLocContact, "name")
                instLocContactName.text = "%s" % (contact.name)

                instLocContactEmail = ElementTree.SubElement(instLocContact, "email")
                instLocContactEmail.text = contact.email

                instLocContactPhone = ElementTree.SubElement(instLocContact, "phone")
                instLocContactPhone.text = contact.phone

            instLocSSID = ElementTree.SubElement(instLocation, "SSID")
            instLocSSID.text = serviceloc.SSID

            instLocEncLevel = ElementTree.SubElement(instLocation, "enc_level")
            instLocEncLevel.text = ', '.join(serviceloc.enc_level)

            instLocPortRestrict = ElementTree.SubElement(instLocation, "port_restrict")
            instLocPortRestrict.text = ("%s" % serviceloc.port_restrict).lower()

            instLocTransProxy = ElementTree.SubElement(instLocation, "transp_proxy")
            instLocTransProxy.text = ("%s" % serviceloc.transp_proxy).lower()

            instLocIpv6 = ElementTree.SubElement(instLocation, "IPv6")
            instLocIpv6.text = ("%s" % serviceloc.IPv6).lower()

            instLocNAT = ElementTree.SubElement(instLocation, "NAT")
            instLocNAT.text = ("%s" % serviceloc.NAT).lower()

            instLocAP_no = ElementTree.SubElement(instLocation, "AP_no")
            instLocAP_no.text = "%s" % int(serviceloc.AP_no)

            instLocWired = ElementTree.SubElement(instLocation, "wired")
            instLocWired.text = ("%s" % serviceloc.wired).lower()

            for url in serviceloc.url.all():
                instLocUrl = ElementTree.SubElement(
                    instLocation,
                    "%s_URL" % (url.urltype)
                )
                instLocUrl.attrib["lang"] = url.lang
                instLocUrl.text = url.url

    return render_to_response(
        "general/institution.xml",
        {
            "xml": to_xml(root)
        },
        context_instance=RequestContext(request,),
        content_type="application/xml"
    )


@never_cache
def realmxml(request):
    realm = Realm.objects.all()[0]
    ElementTree._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ElementTree.Element("realms")
    ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(ns_xsi + "noNamespaceSchemaLocation", "realm.xsd")
    realmElement = ElementTree.SubElement(root, "realm")

    realmCountry = ElementTree.SubElement(realmElement, "country")
    realmCountry.text = realm.country.upper()

    realmStype = ElementTree.SubElement(realmElement, "stype")
    realmStype.text = "%s" % realm.stype

    for name in realm.org_name.all():
        realmOrgName = ElementTree.SubElement(realmElement, "org_name")
        realmOrgName.attrib["lang"] = name.lang
        realmOrgName.text = u"%s" % name.name

    realmAddress = ElementTree.SubElement(realmElement, "address")

    realmAddrStreet = ElementTree.SubElement(realmAddress, "street")
    realmAddrStreet.text = realm.address_street

    realmAddrCity = ElementTree.SubElement(realmAddress, "city")
    realmAddrCity.text = realm.address_city

    for contact in realm.contact.all():
        realmContact = ElementTree.SubElement(realmElement, "contact")

        realmContactName = ElementTree.SubElement(realmContact, "name")
        realmContactName.text = "%s" % (contact.name)

        realmContactEmail = ElementTree.SubElement(realmContact, "email")
        realmContactEmail.text = contact.email

        realmContactPhone = ElementTree.SubElement(realmContact, "phone")
        realmContactPhone.text = contact.phone

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

    return render_to_response(
        "general/realm.xml",
        {"xml": to_xml(root)},
        context_instance=RequestContext(request,),
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
    nIdpCountry.text = "%s" % len(realm.institution_set.filter(ertype=1))

    nSPCountry = ElementTree.SubElement(realmdataElement, "number_SP")
    nSPCountry.text = "%s" % len(realm.institution_set.filter(ertype=2))

    nSPIdpCountry = ElementTree.SubElement(realmdataElement, "number_SPIdP")
    nSPIdpCountry.text = "%s" % len(realm.institution_set.filter(ertype=3))

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
    return render_to_response(
        "general/realm_data.xml",
        {"xml": to_xml(root)},
        context_instance=RequestContext(request,),
        content_type="application/xml"
    )


@never_cache
def servdata(request):
    root = {}
    hosts = InstServer.objects.all()
    insts = Institution.objects.all()

    clients = hosts.filter(ertype__in=[2, 3])
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

    servers = hosts.filter(ertype__in=[1, 3])
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
        if inst.ertype in (2, 3):
            inst_clients = inst.servers.filter(ertype__in=[2, 3])
            if inst_clients:
                inst_dict['clients'] = [getSrvIdentifier(srv, "client_") for
                                        srv in inst_clients]
        if inst.ertype in (1, 3):
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
        (u.userprofile.institution.get_name('el'),
         u.first_name + " " + u.last_name,
         m)
        for u in users if
        u.registrationprofile.activation_key == "ALREADY_ACTIVATED"
        for m in u.email.split(';')
    ]
    data.sort(key=lambda d: unicode(d[0]))
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
    cl = r.headers.get('content-length', None)
    cd = r.headers.get('content-disposition', None)
    if ct.startswith('text/html') and cl != '0' and r.content[0] in ['{', '[']:
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
    if cd is not None:
        resp.setdefault('Content-Disposition', cd)
    return resp
    
def to_xml(ele, encoding="UTF-8"):
    '''
    Convert and return the XML for an *ele*
    (:class:`~xml.etree.ElementTree.Element`)
    with specified *encoding*.'''
    xml = ElementTree.tostring(ele, encoding)
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
        servers = servers.filter(ertype__in=[1, 3])
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

def get_i18n_name(i18n_name, lang, default_lang='en', default_name='unknown'):
    names = i18n_name.filter(lang=lang)
    if names.count()==0:
        names = i18n_name.filter(lang=default_lang)
    if names.count()==0:
        return default_name
    else:
        # follow ServiceLoc.get_name()
        return ', '.join([i.name for i in names])

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
