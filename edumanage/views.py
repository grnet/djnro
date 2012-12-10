# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from edumanage.models import *
from accounts.models import *
from edumanage.forms import *
from django import forms
from django.forms.models import modelformset_factory
from django.forms.models import inlineformset_factory
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.core.mail.message import EmailMessage
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
import json, bz2
import math, datetime
from xml.etree import ElementTree as ET

from django.conf import settings
from django.contrib import messages

from django.db.models import Max

from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from django.contrib.auth import authenticate, login
from registration.models import RegistrationProfile
from django.core.cache import cache

@never_cache
def index(request):
    return render_to_response('front/index.html', context_instance=RequestContext(request))


@login_required
@never_cache
def manage(request):
    services_list = []
    servers_list = []
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return render_to_response('edumanage/welcome.html',
                              context_instance=RequestContext(request, base_response(request)))
        
    services = ServiceLoc.objects.filter(institutionid=inst)
    services_list.extend([s for s in services])
    servers = InstServer.objects.filter(instid=inst)
    servers_list.extend([s for s in servers])
    return render_to_response('edumanage/welcome.html', 
                              {
                               'institution': inst, 
                               'services': services_list,
                               'servers': servers_list
                               },  
                              context_instance=RequestContext(request, base_response(request)))

@login_required
@never_cache
def institutions(request):
    user = request.user
    dict = {}
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    dict['institution'] = inst.pk
    form = InstDetailsForm(initial=dict)
    form.fields['institution'].widget.attrs['readonly'] = True
    return render_to_response('edumanage/institution.html', 
                              {
                               'institution': inst,
                               'form': form, 
                               },  
                              context_instance=RequestContext(request, base_response(request)))



@login_required
@never_cache
def add_institution_details(request, institution_pk):
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    
    if institution_pk and int(inst.pk) != int(institution_pk):
        messages.add_message(request, messages.ERROR, 'You have no rights on this Institution')
        return HttpResponseRedirect(reverse("institutions"))
    
    if request.method == "GET":
        try:         
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(instance=inst_details)
            UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFactInst, can_delete=True)
            urls_form = UrlFormSet(prefix='urlsform', instance = inst_details) 
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm()
            form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            UrlFormSet =  generic_inlineformset_factory(URL_i18n, extra=2, can_delete=True)
            urls_form = UrlFormSet(prefix='urlsform')

        
        form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
        return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form, 'urls_form':urls_form},
                                  context_instance=RequestContext(request, base_response(request)))
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
            urls_inst = urls_form.save()
            return HttpResponseRedirect(reverse("institutions"))
        else:
            form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
            return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form, 'urls_form': urls_form},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def services(request, service_pk):
    user = request.user
    dict = {}
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [2,3]:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Location. Your institution should be either SP or IdP/SP')
        return render_to_response('edumanage/services.html', { 'institution': inst },
                              context_instance=RequestContext(request, base_response(request)))
    try:
        services = ServiceLoc.objects.filter(institutionid = inst)
    except ServiceLoc.DoesNotExist:
        services = False 
    
    if service_pk:
        try:
            services = services.get(pk=service_pk)
        except:
            messages.add_message(request, messages.ERROR, 'You have no rights to view this location')
            return HttpResponseRedirect(reverse("services"))
        return render_to_response('edumanage/service_details.html', 
                              {
                               'institution': inst,
                               'service': services,
                               },  
                              context_instance=RequestContext(request, base_response(request)))
    
    return render_to_response('edumanage/services.html', 
                              {
                               'institution': inst,
                               'services': services, 
                               },  
                              context_instance=RequestContext(request, base_response(request)))



@login_required
@never_cache
def add_services(request, service_pk):
    user = request.user
    service = False
    edit = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [2,3]:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Service. Your institution should be either SP or IdP/SP')
        return render_to_response('edumanage/services_edit.html', { 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))
    if request.method == "GET":

        # Determine add or edit
        try:         
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(instance=service)
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm()
            if service_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this location')
                return HttpResponseRedirect(reverse("services"))
        form.fields['institutionid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        UrlFormSet =  generic_inlineformset_factory(URL_i18n, extra=2, can_delete=True)
        NameFormSet = generic_inlineformset_factory(Name_i18n, extra=2, can_delete=True)
        urls_form = UrlFormSet(prefix='urlsform')
        names_form = NameFormSet(prefix='namesform')
        if (service):
            NameFormSet = generic_inlineformset_factory(Name_i18n, extra=1, formset=NameFormSetFact, can_delete=True)
            names_form = NameFormSet(instance=service, prefix='namesform')
            UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFact, can_delete=True)
            urls_form = UrlFormSet(instance=service, prefix='urlsform')
        form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
        if service:
            edit = True
        for url_form in urls_form.forms:
            url_form.fields['urltype'] = forms.ChoiceField(choices=(('', '----------'),('info', 'Info'),))
        return render_to_response('edumanage/services_edit.html', { 'form': form, 'services_form':names_form, 'urls_form': urls_form, "edit": edit},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        NameFormSet = generic_inlineformset_factory(Name_i18n, extra=1, formset=NameFormSetFact, can_delete=True)
        UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFact, can_delete=True)
        try:         
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(request_data, instance=service)
            names_form = NameFormSet(request_data, instance=service, prefix='namesform')
            urls_form = UrlFormSet(request_data, instance=service, prefix='urlsform')
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm(request_data)
            names_form = NameFormSet(request_data, prefix='namesform')
            urls_form = UrlFormSet(request_data, prefix='urlsform')
            if service_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this location')
                return HttpResponseRedirect(reverse("services"))
        
        if form.is_valid() and names_form.is_valid() and urls_form.is_valid():
            serviceloc = form.save()
            service = serviceloc
            names_form.instance = service
            urls_form.instance = service
            names_inst = names_form.save()
            urls_inst = urls_form.save()
            return HttpResponseRedirect(reverse("services"))
        else:
            form.fields['institutionid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
            form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
        if service:
            edit = True
        for url_form in urls_form.forms:
            url_form.fields['urltype'] = forms.ChoiceField(choices=(('', '----------'),('info', 'Info'),))
        return render_to_response('edumanage/services_edit.html', { 'institution': inst, 'form': form, 'services_form':names_form, 'urls_form': urls_form, "edit": edit},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def del_service(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        service_pk = req_data['service_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete service. Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            service = ServiceLoc.objects.get(institutionid=institution, pk=service_pk)
        except ServiceLoc.DoesNotExist:
            resp['error'] = "Could not get service or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        try:
            service.delete()
        except:
            resp['error'] = "Could not delete service"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Service successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')


@login_required
@never_cache
def servers(request, server_pk):
    user = request.user
    servers = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        servers = InstServer.objects.filter(instid=inst)
    if server_pk:
        servers = servers.get(pk=server_pk)
        return render_to_response('edumanage/server_details.html', 
                              {
                               'institution': inst,
                               'server': servers,
                               },  
                              context_instance=RequestContext(request, base_response(request)))
    return render_to_response('edumanage/servers.html', { 'servers': servers},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def add_server(request, server_pk):
    user = request.user
    server = False
    edit = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
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
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this server')
                return HttpResponseRedirect(reverse("servers"))  
        form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        if server:
            edit = True
                      
        return render_to_response('edumanage/servers_edit.html', { 'form': form, 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            server = InstServer.objects.get(instid=inst, pk=server_pk)
            form = InstServerForm(request_data, instance=server)
        except InstServer.DoesNotExist:
            form = InstServerForm(request_data)
            if server_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this server')
                return HttpResponseRedirect(reverse("servers")) 
        
        if form.is_valid():
            instserverf = form.save()
            return HttpResponseRedirect(reverse("servers"))
        else:
            form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        if server:
            edit = True
        return render_to_response('edumanage/servers_edit.html', { 'institution': inst, 'form': form, 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def del_server(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        server_pk = req_data['server_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete server. Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            server = InstServer.objects.get(instid=institution, pk=server_pk)
        except InstServer.DoesNotExist:
            resp['error'] = "Could not get server or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        try:
            server.delete()
        except:
            resp['error'] = "Could not delete server"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Server successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')


@login_required
@never_cache
def realms(request):
    user = request.user
    servers = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        realms = InstRealm.objects.filter(instid=inst)
    if inst.ertype not in [1,3]:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Realms. Your institution should be either IdP or IdP/SP')
    return render_to_response('edumanage/realms.html', { 'realms': realms },
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def add_realm(request, realm_pk):
    user = request.user
    server = False
    realm = False
    edit = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst.ertype not in [1,3]:
        messages.add_message(request, messages.ERROR, 'Cannot add/edit Realm. Your institution should be either IdP or IdP/SP')
        return render_to_response('edumanage/realms_edit.html', { 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))
    if request.method == "GET":

        # Determine add or edit
        try:         
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm()
            if realm_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this realm')
                return HttpResponseRedirect(reverse("realms"))
        form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        form.fields['proxyto'] = forms.ModelMultipleChoiceField(queryset=InstServer.objects.filter(pk__in=getInstServers(inst)))
        if realm:
            edit = True
        return render_to_response('edumanage/realms_edit.html', { 'form': form, 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(request_data, instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm(request_data)
            if realm_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this realm')
                return HttpResponseRedirect(reverse("realms")) 
        if form.is_valid():
            instserverf = form.save()
            return HttpResponseRedirect(reverse("realms"))
        else:
            form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
            form.fields['proxyto'] = forms.ModelMultipleChoiceField(queryset=InstServer.objects.filter(pk__in=getInstServers(inst)))
        if realm:
            edit = True
        return render_to_response('edumanage/realms_edit.html', { 'institution': inst, 'form': form, 'edit': edit },
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def del_realm(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        realm_pk = req_data['realm_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            realm = InstRealm.objects.get(instid=institution, pk=realm_pk)
        except InstRealm.DoesNotExist:
            resp['error'] = "Could not get realm or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        try:
            realm.delete()
        except:
            resp['error'] = "Could not delete realm"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Realm successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')


@login_required
@never_cache
def contacts(request):
    user = request.user
    servers = False
    instcontacts = []
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        instcontacts.extend([x.contact.pk for x in InstitutionContactPool.objects.filter(institution=inst)])
        contacts = Contact.objects.filter(pk__in=instcontacts)
    return render_to_response('edumanage/contacts.html', { 'contacts': contacts},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def add_contact(request, contact_pk):
    user = request.user
    server = False
    edit = False
    contact = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":

        # Determine add or edit
        try:         
            contactinst = InstitutionContactPool.objects.get(institution=inst, contact__pk=contact_pk)
            contact = contactinst.contact
            form = ContactForm(instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm()
            if contact_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this contact')
                return HttpResponseRedirect(reverse("contacts"))
        if contact:
            edit = True
        return render_to_response('edumanage/contacts_edit.html', { 'form': form, "edit" : edit},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            contactinst = InstitutionContactPool.objects.get(institution=inst, contact__pk=contact_pk)
            contact = contactinst.contact
            form = ContactForm(request_data, instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm(request_data)
            if contact_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this contact')
                return HttpResponseRedirect(reverse("contacts"))
        
        if form.is_valid():
            contact = form.save()
            instContPool, created = InstitutionContactPool.objects.get_or_create(contact=contact, institution=inst)
            instContPool.save()
            return HttpResponseRedirect(reverse("contacts"))
        if contact:
            edit = True
        return render_to_response('edumanage/contacts_edit.html', { 'form': form, "edit": edit},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
@never_cache
def del_contact(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        contact_pk = req_data['contact_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete contact. Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            contactinst = InstitutionContactPool.objects.get(institution=institution, contact__pk=contact_pk)
            contact = contactinst.contact
        except InstitutionContactPool.DoesNotExist:
            resp['error'] = "Could not get contact or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        try:
            for service in ServiceLoc.objects.filter(institutionid=institution):
                if (contact in service.contact.all() and len(service.contact.all()) == 1):
                    resp['error'] = "Could not delete contact. It is the only contact in service <b>%s</b>.<br>Fix it and try again" %service.get_name(lang="en")
                    return HttpResponse(json.dumps(resp), mimetype='application/json')
            if (contact in institution.institutiondetails.contact.all() and len(institution.institutiondetails.contact.all()) == 1):
                    resp['error'] = "Could not delete contact. It is the only contact your institution.<br>Fix it and try again"
                    return HttpResponse(json.dumps(resp), mimetype='application/json')
            contact.delete()
        except Exception:
            resp['error'] = "Could not delete contact"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')


@login_required
@never_cache
def instrealmmon(request):
    user = request.user
    servers = False
    instcontacts = []
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if inst:
        instrealmmons = InstRealmMon.objects.filter(realm__instid=inst)
    return render_to_response('edumanage/instrealmmons.html', { 'realms': instrealmmons},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
@never_cache
def add_instrealmmon(request, instrealmmon_pk):
    user = request.user
    instrealmmon = False
    edit = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":
        # Determine add or edit
        try:         
            instrealmmon = InstRealmMon.objects.get(pk=instrealmmon_pk, realm__instid=inst)
            form = InstRealmMonForm(instance=instrealmmon)
        except InstRealmMon.DoesNotExist:
            form = InstRealmMonForm()
            if instrealmmon_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm')
                return HttpResponseRedirect(reverse("instrealmmon"))
        if instrealmmon:
            edit = True
        form.fields['realm'] = forms.ModelChoiceField(queryset=InstRealm.objects.filter(instid=inst.pk).exclude(realm__startswith="*"), empty_label=None)
        return render_to_response('edumanage/instrealmmon_edit.html', { 'form': form, "edit" : edit},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            instrealmmon = InstRealmMon.objects.get(pk=instrealmmon_pk, realm__instid=inst)
            form = InstRealmMonForm(request_data, instance=instrealmmon)
        except InstRealmMon.DoesNotExist:
            form = InstRealmMonForm(request_data)
            if instrealmmon_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm')
                return HttpResponseRedirect(reverse("instrealmmon"))
        if form.is_valid():
            instrealmmonobj = form.save()
            return HttpResponseRedirect(reverse("instrealmmon"))
        if instrealmmon:
            edit = True
        form.fields['realm'] = forms.ModelChoiceField(queryset=InstRealm.objects.filter(instid=inst.pk).exclude(realm__startswith="*"), empty_label=None)
        return render_to_response('edumanage/instrealmmon_edit.html', { 'form': form, "edit": edit},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
@never_cache
def del_instrealmmon(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        instrealmmon_pk = req_data['instrealmmon_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete monitored realm. Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            instrealmmon = InstRealmMon.objects.get(pk=instrealmmon_pk, realm__instid=institution)
            instrealmmon.delete()
        except InstRealmMon.DoesNotExist:
            resp['error'] = "Could not get monitored realm or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')

@login_required
@never_cache
def add_monlocauthpar(request, instrealmmon_pk, monlocauthpar_pk):
    user = request.user
    monlocauthpar = False
    edit = False
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    try:
        instdetails = inst.institutiondetails
    except InstitutionDetails.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))
    if request.method == "GET":
        # Determine add or edit
        try:
            instrealmmon = InstRealmMon.objects.get(pk=instrealmmon_pk, realm__instid=inst)
            monlocauthpar = MonLocalAuthnParam.objects.get(pk=monlocauthpar_pk, instrealmmonid__realm__instid=inst)
            form = MonLocalAuthnParamForm(instance=monlocauthpar)
        except MonLocalAuthnParam.DoesNotExist:
            form = MonLocalAuthnParamForm()
            if monlocauthpar_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm Parameters')
                return HttpResponseRedirect(reverse("instrealmmon"))
        except InstRealmMon.DoesNotExist:
            if instrealmmon_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm Parameters')
            return HttpResponseRedirect(reverse("instrealmmon"))
        if monlocauthpar:
            edit = True
        form.fields['instrealmmonid'] = forms.ModelChoiceField(queryset=InstRealmMon.objects.filter(pk=instrealmmon.pk), empty_label=None)
        return render_to_response('edumanage/monlocauthpar_edit.html', { 'form': form, "edit" : edit, "realm":instrealmmon },
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            instrealmmon = InstRealmMon.objects.get(pk=instrealmmon_pk, realm__instid=inst)
            monlocauthpar = MonLocalAuthnParam.objects.get(pk=monlocauthpar_pk, instrealmmonid__realm__instid=inst)
            form = MonLocalAuthnParamForm(request_data, instance=monlocauthpar)
        except MonLocalAuthnParam.DoesNotExist:
            form = MonLocalAuthnParamForm(request_data)
            if monlocauthpar_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm Parameters')
                return HttpResponseRedirect(reverse("instrealmmon"))
        except InstRealmMon.DoesNotExist:
            if instrealmmon_pk:
                messages.add_message(request, messages.ERROR, 'You have no rights to edit this Monitoring Realm Parameters')
            return HttpResponseRedirect(reverse("instrealmmon"))
        if form.is_valid():
            monlocauthparobj = form.save()
            return HttpResponseRedirect(reverse("instrealmmon"))
        if monlocauthpar:
            edit = True
        form.fields['instrealmmonid'] = forms.ModelChoiceField(queryset=InstRealmMon.objects.filter(pk=instrealmmon.pk), empty_label=None)
        return render_to_response('edumanage/monlocauthpar_edit.html', { 'form': form, "edit": edit, "realm":instrealmmon},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
@never_cache
def del_monlocauthpar(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        monlocauthpar_pk = req_data['monlocauthpar_pk']
        try:
            profile = user.get_profile()
            institution = profile.institution
        except UserProfile.DoesNotExist:
            resp['error'] = "Could not delete realm monitoring parameters. Not enough rights"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp = {}
        try:
            monlocauthpar = MonLocalAuthnParam.objects.get(pk=monlocauthpar_pk, instrealmmonid__realm__instid=institution)
            monlocauthpar.delete()
        except MonLocalAuthnParam.DoesNotExist:
            resp['error'] = "Could not get realm monitoring parameters or you have no rights to delete"
            return HttpResponse(json.dumps(resp), mimetype='application/json')
        resp['success'] = "Contact successfully deleted"
        return HttpResponse(json.dumps(resp), mimetype='application/json')

@login_required
@never_cache
def adduser(request):
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        return HttpResponseRedirect(reverse("manage"))

    if request.method == "GET":
        form = ContactForm()
        return render_to_response('edumanage/add_user.html', { 'form' : form },
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        form = ContactForm(request_data)
        if form.is_valid():
            contact = form.save()
            instContPool = InstitutionContactPool(contact=contact, institution=inst)
            instContPool.save()
            response_data = {}
            response_data['value'] = "%s" %contact.pk
            response_data['text'] = "%s" %contact
            return HttpResponse(json.dumps(response_data), mimetype='application/json')
        else:
            return render_to_response('edumanage/add_user.html', {'form': form,},
                                      context_instance=RequestContext(request, base_response(request)))


@login_required
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
    try:
        profile = user.get_profile()
        institution = profile.institution
        institution_exists = True
    except UserProfile.DoesNotExist:
        institution_exists = False
    try:
        inst.append(institution)
        server = InstServer.objects.filter(instid=institution)
        services = ServiceLoc.objects.filter(institutionid=institution)
        instrealms = InstRealm.objects.filter(instid=institution)
        instcontacts.extend([x.contact.pk for x in InstitutionContactPool.objects.filter(institution=institution)])
        contacts = Contact.objects.filter(pk__in=instcontacts)
        instrealmmons = InstRealmMon.objects.filter(realm__instid=institution)
    except:
        pass
    try:
        instututiondetails = institution.institutiondetails
    except:
        instututiondetails = False
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
            
        }


@login_required
@never_cache
def get_service_points(request):
    if request.method == "GET":
        user = request.user
        try:
            profile = user.get_profile()
            inst = profile.institution
        except UserProfile.DoesNotExist:
            inst = False
            return HttpResponseNotFound('<h1>Something went really wrong</h1>')
        servicelocs = ServiceLoc.objects.filter(institutionid=inst)
        
        locs = []
        for sl in servicelocs:
            response_location = {}
            response_location['lat'] = u"%s"%sl.latitude
            response_location['lng'] = u"%s"%sl.longitude
            response_location['address'] = u"%s<br>%s"%(sl.address_street, sl.address_city)
            if len(sl.enc_level[0]) != 0:
                response_location['enc'] = u"%s"%(','.join(sl.enc_level))
            else:
                response_location['enc'] = u"-"
            response_location['AP_no'] = u"%s"%(sl.AP_no)
            response_location['name'] = sl.loc_name.get(lang='en').name
            response_location['port_restrict'] = u"%s"%(sl.port_restrict)
            response_location['transp_proxy'] = u"%s"%(sl.transp_proxy)
            response_location['IPv6'] = u"%s"%(sl.IPv6)
            response_location['NAT'] = u"%s"%(sl.NAT)
            response_location['wired'] = u"%s"%(sl.wired)
            response_location['SSID'] = u"%s"%(sl.SSID)
            response_location['key'] = u"%s"%sl.pk
            locs.append(response_location)
        return HttpResponse(json.dumps(locs), mimetype='application/json')
    else:
       return HttpResponseNotFound('<h1>Something went really wrong</h1>')

@never_cache
def get_all_services(request):
    lang = request.LANGUAGE_CODE
    servicelocs = ServiceLoc.objects.all()
    locs = []
    for sl in servicelocs:
        response_location = {}
        response_location['lat'] = u"%s"%sl.latitude
        response_location['lng'] = u"%s"%sl.longitude
        response_location['address'] = u"%s<br>%s"%(sl.address_street, sl.address_city)
        if len(sl.enc_level[0]) != 0:
            response_location['enc'] = u"%s"%(','.join(sl.enc_level))
        else:
            response_location['enc'] = u"-"
        response_location['AP_no'] = u"%s"%(sl.AP_no)
        try:
            response_location['inst'] = sl.institutionid.org_name.get(lang=lang).name
        except Name_i18n.DoesNotExist:
            response_location['inst'] = sl.institutionid.org_name.get(lang='en').name
        try:
            response_location['name'] = sl.loc_name.get(lang=lang).name
        except Name_i18n.DoesNotExist:
            response_location['name'] = sl.loc_name.get(lang='en').name
        response_location['port_restrict'] = u"%s"%(sl.port_restrict)
        response_location['transp_proxy'] = u"%s"%(sl.transp_proxy)
        response_location['IPv6'] = u"%s"%(sl.IPv6)
        response_location['NAT'] = u"%s"%(sl.NAT)
        response_location['wired'] = u"%s"%(sl.wired)
        response_location['SSID'] = u"%s"%(sl.SSID)
        response_location['key'] = u"%s"%sl.pk
        locs.append(response_location)
    return HttpResponse(json.dumps(locs), mimetype='application/json')

@never_cache
def user_login(request):
    try:
        error_username = False
        error_orgname = False
        error_entitlement = False
        error_mail = False
        has_entitlement = False
        error = ''
        username = request.META['HTTP_EPPN']
        if not username:
            error_username = True
        firstname = request.META['HTTP_SHIB_INETORGPERSON_GIVENNAME']
        lastname = request.META['HTTP_SHIB_PERSON_SURNAME']
        if 'mail' in request.META:
            mail = request.META['mail']
        elif ('HTTP_MAIL' in request.META):
            mail = request.META['HTTP_MAIL']
        elif ('HTTP_SHIB_INETORGPERSON_MAIL' in request.META):
            mail = request.META['HTTP_SHIB_INETORGPERSON_MAIL']
        else:
            mail = ''

        #organization = request.META['HTTP_SHIB_HOMEORGANIZATION']
        entitlement = request.META['HTTP_SHIB_EP_ENTITLEMENT']
        if settings.SHIB_AUTH_ENTITLEMENT in entitlement.split(";"):
            has_entitlement = True
        if not has_entitlement:
            error_entitlement = True
#        if not organization:
#            error_orgname = True
        if not mail:
            error_mail = True
        if error_username:
            error = _("Your idP should release the eduPersonPrincipalName attribute towards this service<br>")
        if error_entitlement:
            error = error + _("Your idP should release an appropriate eduPersonEntitlement attribute towards this service<br>")
        if error_mail:
            error = error + _("Your idP should release the mail attribute towards this service")
        if error_username or error_orgname or error_entitlement or error_mail:
            return render_to_response('status.html', {'error': error, "missing_attributes": True},
                                  context_instance=RequestContext(request))
        try:
            user = User.objects.get(username__exact=username)
            user.email = mail
            user.first_name = firstname
            user.last_name = lastname
            user.save()
            user_exists = True
        except User.DoesNotExist:
            user_exists = False
        user = authenticate(username=username, firstname=firstname, lastname=lastname, mail=mail, authsource='shibboleth')
        if user is not None:
            try:
                profile = user.get_profile()
                inst = profile.institution
            except UserProfile.DoesNotExist:
                form = UserProfileForm()
                form.fields['user'] = forms.ModelChoiceField(queryset=User.objects.filter(pk=user.pk), empty_label=None)
                form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.all(), empty_label=None)
                return render_to_response('registration/select_institution.html', {'form': form}, context_instance=RequestContext(request))
            if user.is_active:
               login(request, user)
               return HttpResponseRedirect(reverse("manage"))
            else:
                status = _("User account <strong>%s</strong> is pending activation. Administrators have been notified and will activate this account within the next days. <br>If this account has remained inactive for a long time contact your technical coordinator or GRNET Helpdesk") %user.username
                return render_to_response('status.html', {'status': status, 'inactive': True},
                                  context_instance=RequestContext(request))
        else:
            error = _("Something went wrong during user authentication. Contact your administrator %s" %user)
            return render_to_response('status.html', {'error': error,},
                                  context_instance=RequestContext(request))
    except Exception as e:
        error = _("Invalid login procedure. Error: %s"%e)
        return render_to_response('status.html', {'error': error,},
                                  context_instance=RequestContext(request))

@never_cache
def geolocate(request):
    return render_to_response('front/geolocate.html',
                                  context_instance=RequestContext(request))
@never_cache
def participants(request):
    institutions = Institution.objects.all()
    dets = []
    for i in institutions:
        try:
            dets.append(i.institutiondetails)
        except InstitutionDetails.DoesNotExist:
            pass
    return render_to_response('front/participants.html', {'institutions': dets},
                                  context_instance=RequestContext(request))
@never_cache
def selectinst(request):
    if request.method == 'POST':
        request_data = request.POST.copy()
        user = request_data['user']
        try:
            existingProfile = UserProfile.objects.get(user=user)
            error = _("Violation warning: User account is already associated with an institution.The event has been logged and our administrators will be notified about it")
            return render_to_response('status.html', {'error': error, 'inactive': True},
                                  context_instance=RequestContext(request))
        except UserProfile.DoesNotExist:
            pass
            
        form = UserProfileForm(request_data)
        if form.is_valid():
            userprofile = form.save()
            user_activation_notify(userprofile)
            error = _("User account <strong>%s</strong> is pending activation. Administrators have been notified and will activate this account within the next days. <br>If this account has remained inactive for a long time contact your technical coordinator or GRNET Helpdesk") %userprofile.user.username
            return render_to_response('status.html', {'status': error, 'inactive': True},
                                  context_instance=RequestContext(request))
        else:
            form.fields['user'] = forms.ModelChoiceField(queryset=User.objects.filter(pk=user.pk), empty_label=None)
            form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.all(), empty_label=None)
            return render_to_response('registration/select_institution.html', {'form': form}, context_instance=RequestContext(request))


def user_activation_notify(userprofile):
    current_site = Site.objects.get_current()
    subject = render_to_string('registration/activation_email_subject.txt',
                                   { 'site': current_site })
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    registration_profile = RegistrationProfile.objects.create_profile(userprofile.user)
    message = render_to_string('registration/activation_email.txt',
                                   { 'activation_key': registration_profile.activation_key,
                                     'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                                     'site': current_site,
                                     'user': userprofile.user,
                                     'institution': userprofile.institution })
    send_new_mail(settings.EMAIL_SUBJECT_PREFIX + subject, 
                              message, settings.SERVER_EMAIL,
                             settings.NOTIFY_ADMIN_MAILS, [])
@never_cache
def closest(request):
    if request.method == 'GET':
        locs = []
        request_data = request.GET.copy()
        response_location = {}
        if 'lat' in request.GET and 'lng' in request.GET:
            response_location["lat"] = request_data['lat']
            response_location["lng"] = request_data['lng']
        else:
            response = {"status":"Cannot parse a request without longitude or latitude. Use ?lng=<langitude>&lat=<latitude>&_=<random_num> in your query"}
            return HttpResponse(json.dumps(response), mimetype='application/json')
        lat = float(request_data['lat'])
        lng = float(request_data['lng'])
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
            dLat = rad(float(pointlat)-float(lat))
            dLong = rad(float(pointlng)-float(lng))
            a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(rad(lat)) * math.cos(rad(float(pointlat))) * math.sin(dLong/2) * math.sin(dLong/2) 
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            d = R * c
            distances[counter] = d
            if (closest == -1 or d < distances[closest]):
                closest = counter
                closestMarker = {"name": pointname, "lat": pointlat, "lng": pointlng, "text": pointtext}
        return HttpResponse(json.dumps(closestMarker), mimetype='application/json')
    else:
        response = {"status":"Use a GET method for your request"}
        return HttpResponse(json.dumps(response), mimetype='application/json')

@never_cache
def worldPoints(request):
    if request.method == 'GET':
        points = getPoints()
        return HttpResponse(json.dumps(points), mimetype='application/json')

@never_cache
def world(request):
        return render_to_response('front/world.html',
                                  context_instance=RequestContext(request))


@never_cache
def managementPage(request):
    return render_to_response('front/management.html',
                                  context_instance=RequestContext(request))

def getPoints():
    points = cache.get('points')
    if points:
        points = bz2.decompress(points)
        return json.loads(points)
    else:
        point_list = []
        doc = ET.parse(settings.KML_FILE)
        root = doc.getroot()
        r = root.getchildren()[0]
        for (counter, i) in enumerate(r.getchildren()):
            if "id" in i.keys():
                j = i.getchildren()
                pointname = j[0].text
                point = j[2].getchildren()[0].text
                pointlng, pointlat, pointele = point.split(',')
                Marker = {"name": pointname, "lat": pointlat, "lng": pointlng, "text": j[1].text}
                point_list.append(Marker);
        points = json.dumps(point_list)
        cache.set('points', bz2.compress(points), 60 * 3600 * 24)
        return json.loads(points)


@never_cache
def instxml(request):
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("institutions")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "institution.xsd")
    #root.attrib["xsi:noNamespaceSchemaLocation"] = "institution.xsd"
    institutions = Institution.objects.all()
    for institution in institutions:
        try:
            inst = institution.institutiondetails
            if not inst:
                pass
        except InstitutionDetails.DoesNotExist:
            pass
        
        instElement = ET.SubElement(root, "institution")
        
        instCountry = ET.SubElement(instElement, "country")
        instCountry.text = ("%s" %inst.institution.realmid.country).upper()
        
        instType = ET.SubElement(instElement, "type")
        instType.text = "%s" %inst.institution.ertype
        
        for realm in institution.instrealm_set.all():
            instRealm = ET.SubElement(instElement, "inst_realm")
            instRealm.text = realm.realm
        
        for name in inst.institution.org_name.all():
            instOrgName = ET.SubElement(instElement, "org_name")
            instOrgName.attrib["lang"] = name.lang
            instOrgName.text = u"%s" %name.name
        
        instAddress = ET.SubElement(instElement, "address")
        
        instAddrStreet = ET.SubElement(instAddress, "street")
        instAddrStreet.text = inst.address_street
        
        instAddrCity = ET.SubElement(instAddress, "city")
        instAddrCity.text = inst.address_city
        
        for contact in inst.contact.all():
            instContact = ET.SubElement(instElement, "contact")
            
            instContactName = ET.SubElement(instContact, "name")
            instContactName.text = "%s" %(contact.name)
            
            instContactEmail = ET.SubElement(instContact, "email")
            instContactEmail.text = contact.email
            
            instContactPhone = ET.SubElement(instContact, "phone")
            instContactPhone.text = contact.phone
        
        for url in inst.url.all():
            instUrl = ET.SubElement(instElement, "%s_URL"%(url.urltype))
            instUrl.attrib["lang"] = url.lang
            instUrl.text = url.url
        
        instTs = ET.SubElement(instElement, "ts")
        instTs.text = "%s" %inst.ts.isoformat()
        #Let's go to Institution Service Locations

        for serviceloc in inst.institution.serviceloc_set.all():
            instLocation = ET.SubElement(instElement, "location")
            
            instLong = ET.SubElement(instLocation, "longitude")
            instLong.text = "%s" %serviceloc.longitude
            
            instLat = ET.SubElement(instLocation, "latitude")
            instLat.text = "%s" %serviceloc.latitude
            
            for instlocname in serviceloc.loc_name.all():
                instLocName = ET.SubElement(instLocation, "loc_name")
                instLocName.attrib["lang"] = instlocname.lang
                instLocName.text = instlocname.name
            
            instLocAddress = ET.SubElement(instLocation, "address")
        
            instLocAddrStreet = ET.SubElement(instLocAddress, "street")
            instLocAddrStreet.text = serviceloc.address_street
        
            instLocAddrCity = ET.SubElement(instLocAddress, "city")
            instLocAddrCity.text = serviceloc.address_city
            
            for contact in serviceloc.contact.all():
                instLocContact = ET.SubElement(instLocation, "contact")
                
                instLocContactName = ET.SubElement(instLocContact, "name")
                instLocContactName.text = "%s" %(contact.name)
                
                instLocContactEmail = ET.SubElement(instLocContact, "email")
                instLocContactEmail.text = contact.email
                
                instLocContactPhone = ET.SubElement(instLocContact, "phone")
                instLocContactPhone.text = contact.phone
            
            instLocSSID = ET.SubElement(instLocation, "SSID")
            instLocSSID.text = serviceloc.SSID
            
            instLocEncLevel = ET.SubElement(instLocation, "enc_level")
            instLocEncLevel.text = ', '.join(serviceloc.enc_level)
            
            instLocPortRestrict = ET.SubElement(instLocation, "port_restrict")
            instLocPortRestrict.text = ("%s" %serviceloc.port_restrict).lower()
            
            instLocTransProxy = ET.SubElement(instLocation, "transp_proxy")
            instLocTransProxy.text = ("%s" %serviceloc.transp_proxy).lower()
            
            instLocIpv6 = ET.SubElement(instLocation, "IPv6")
            instLocIpv6.text = ("%s" %serviceloc.IPv6).lower()
            
            instLocNAT = ET.SubElement(instLocation, "NAT")
            instLocNAT.text = ("%s" %serviceloc.NAT).lower()
            
            instLocAP_no = ET.SubElement(instLocation, "AP_no")
            instLocAP_no.text = "%s" %int(serviceloc.AP_no)
            
            instLocWired = ET.SubElement(instLocation, "wired")
            instLocWired.text = ("%s" %serviceloc.wired).lower()
            
            for url in serviceloc.url.all():
                instLocUrl = ET.SubElement(instLocation, "%s_URL"%(url.urltype))
                instLocUrl.attrib["lang"] = url.lang
                instLocUrl.text = url.url
            
    return render_to_response("general/institution.xml", {"xml":to_xml(root)},context_instance=RequestContext(request,), mimetype="application/xml")
        
@never_cache
def realmxml(request):
    realm = Realm.objects.all()[0]
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("realms")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "realm.xsd")
    #root.attrib["xsi:noNamespaceSchemaLocation"] = "institution.xsd"
    realmElement = ET.SubElement(root, "realm")
    
    realmCountry = ET.SubElement(realmElement, "country")
    realmCountry.text = realm.country.upper()
        
    realmStype = ET.SubElement(realmElement, "stype")
    realmStype.text = "%s" %realm.stype
    
    for name in realm.org_name.all():
        realmOrgName = ET.SubElement(realmElement, "org_name")
        realmOrgName.attrib["lang"] = name.lang
        realmOrgName.text = u"%s" %name.name
    
    realmAddress = ET.SubElement(realmElement, "address")
        
    realmAddrStreet = ET.SubElement(realmAddress, "street")
    realmAddrStreet.text = realm.address_street
    
    realmAddrCity = ET.SubElement(realmAddress, "city")
    realmAddrCity.text = realm.address_city
    
    for contact in realm.contact.all():
        realmContact = ET.SubElement(realmElement, "contact")
        
        realmContactName = ET.SubElement(realmContact, "name")
        realmContactName.text = "%s" %(contact.name)
        
        realmContactEmail = ET.SubElement(realmContact, "email")
        realmContactEmail.text = contact.email
        
        realmContactPhone = ET.SubElement(realmContact, "phone")
        realmContactPhone.text = contact.phone
    
    for url in realm.url.all():
        realmUrl = ET.SubElement(realmElement, "%s_URL"%(url.urltype))
        realmUrl.attrib["lang"] = url.lang
        realmUrl.text = url.url
    
    instTs = ET.SubElement(realmElement, "ts")
    instTs.text = "%s" %realm.ts.isoformat()
    
    return render_to_response("general/realm.xml", {"xml":to_xml(root)},context_instance=RequestContext(request,), mimetype="application/xml")

@never_cache
def realmdataxml(request):
    realm = Realm.objects.all()[0]
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("realm_data_root")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "realm_data.xsd")
    
    realmdataElement = ET.SubElement(root, "realm_data")
    
    realmCountry = ET.SubElement(realmdataElement, "country")
    realmCountry.text = realm.country.upper()
    
    nIdpCountry = ET.SubElement(realmdataElement, "number_IdP")
    nIdpCountry.text = "%s" %len(realm.institution_set.filter(ertype=1))
    
    nSPCountry = ET.SubElement(realmdataElement, "number_SP")
    nSPCountry.text = "%s" %len(realm.institution_set.filter(ertype=2))
    
    nSPIdpCountry = ET.SubElement(realmdataElement, "number_SPIdP")
    nSPIdpCountry.text = "%s" %len(realm.institution_set.filter(ertype=3))
    
    ninstCountry = ET.SubElement(realmdataElement, "number_inst")
    ninstCountry.text = "%s" %len(realm.institution_set.all())
    
    nuserCountry = ET.SubElement(realmdataElement, "number_user")
    insts = realm.institution_set.all()
    users = 0
    for inst in insts:
        try:
            if inst.institutiondetails.number_user:
                users = users + inst.institutiondetails.number_user
        except InstitutionDetails.DoesNotExist:
            pass
    nuserCountry.text = "%s" %users
    
    nIdCountry = ET.SubElement(realmdataElement, "number_id")
    insts = realm.institution_set.all()
    ids = 0
    for inst in insts:
        try:
            if inst.institutiondetails.number_id:
                ids = ids + inst.institutiondetails.number_id
        except InstitutionDetails.DoesNotExist:
            pass
    nIdCountry.text = "%s" %ids
    
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
    instTs = ET.SubElement(realmdataElement, "ts")
    instTs.text = "%s" %max(datetimes).isoformat()
    
    
    return render_to_response("general/realm_data.xml", {"xml":to_xml(root)},context_instance=RequestContext(request,), mimetype="application/xml")

def to_xml(ele, encoding="UTF-8"):
    "Convert and return the XML for an *ele* (:class:`~xml.etree.ElementTree.Element`) with specified *encoding*."
    xml = ET.tostring(ele, encoding)
    return xml if xml.startswith('<?xml') else '<?xml version="1.0" encoding="%s"?>%s' % (encoding, xml)
    
def getInstContacts(inst):
    contacts = InstitutionContactPool.objects.filter(institution=inst)
    contact_pks = []
    for contact in contacts:
        contact_pks.append(contact.contact.pk)
    return list(set(contact_pks))

def getInstServers(inst):
    servers = InstServer.objects.filter(instid=inst)
    server_pks = []
    for server in servers:
        server_pks.append(server.pk)
    return list(set(server_pks))


def rad(x):
    return x*math.pi/180

def send_new_mail(subject, message, from_email, recipient_list, bcc_list):
    return EmailMessage(subject, message, from_email, recipient_list, bcc_list).send()

