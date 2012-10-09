# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from edumanage.models import *
from edumanage.forms import *
from django import forms
from django.forms.models import modelformset_factory
from django.forms.models import inlineformset_factory
from django.contrib.contenttypes.generic import generic_inlineformset_factory
import json 
import math
from xml.etree import cElementTree as ET

from django.conf import settings

def index(request):
    return render_to_response('front/index.html', context_instance=RequestContext(request, base_response(request)))

@login_required
def manage(request):
    services_list = []
    servers_list = []
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
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
def institutions(request):
    user = request.user
    dict = {}
    
    try:
        profile = user.get_profile()
        inst = profile.institution
        inst.__unicode__ = inst.get_name(request.LANGUAGE_CODE)
    except UserProfile.DoesNotExist:
        inst = False
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
def add_institution_details(request, institution_pk):
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
        
    if (not inst) or (int(inst.pk) != int(institution_pk)):
    #            messages.add_message(request, messages.WARNING,
    #                             _("Insufficient rights on Institution. Contact your administrator"))
        return HttpResponseRedirect(reverse("institutions"))
    if request.method == "GET":

        # Determine add or edit
        request_data = request.POST.copy()
        try:         
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(instance=inst_details)
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm()
            form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
        
        
        return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(request_data, instance=inst_details)
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm(request_data)
        if form.is_valid():
            instdets = form.save()
            return HttpResponseRedirect(reverse("institutions"))
        else:
            try:
                profile = user.get_profile()
                inst = profile.institution
            except UserProfile.DoesNotExist:
                inst = False
                form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
def services(request):
    user = request.user
    dict = {}
    
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
    try:
        services = ServiceLoc.objects.filter(institutionid = inst)
    except ServiceLoc.DoesNotExist:
        services = False 
        
    
    return render_to_response('edumanage/services.html', 
                              {
                               'institution': inst,
                               'services': services, 
                               },  
                              context_instance=RequestContext(request, base_response(request)))



@login_required
def add_services(request, service_pk):
    user = request.user
    service = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False

    if request.method == "GET":

        # Determine add or edit
        try:         
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(instance=service)
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm()
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
        return render_to_response('edumanage/services_edit.html', { 'form': form, 'services_form':names_form, 'urls_form': urls_form},
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
        
        if form.is_valid() and names_form.is_valid() and urls_form.is_valid():
            serviceloc = form.save()
            service = serviceloc
            names_form.instance = service
            urls_form.instance = service
            names_inst = names_form.save()
            urls_inst = urls_form.save()
#            for nform in names_inst:
#                nform.content_object = serviceloc
#                nform.save()
#            for uform in urls_inst:
#                uform.content_object = serviceloc
#                uform.save()
            return HttpResponseRedirect(reverse("services"))
        else:
            form.fields['institutionid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)

        return render_to_response('edumanage/services_edit.html', { 'institution': inst, 'form': form, 'services_form':names_form, 'urls_form': urls_form},
                                  context_instance=RequestContext(request, base_response(request)))



@login_required
def get_service_points(request):
    if request.method == "GET":
        user = request.user
        try:
            profile = user.get_profile()
            inst = profile.institution
        except UserProfile.DoesNotExist:
            inst = False
        servicelocs = ServiceLoc.objects.filter(institutionid=inst)
        
        locs = []
        for sl in servicelocs:
            response_location = {}
            response_location['lat'] = u"%s"%sl.latitude
            response_location['lng'] = u"%s"%sl.longitude
            response_location['address'] = u"%s<br>%s"%(sl.address_street, sl.address_city)
            response_location['enc'] = u"%s"%(sl.enc_level)
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


def get_all_services(request):
    servicelocs = ServiceLoc.objects.all()
    locs = []
    for sl in servicelocs:
        response_location = {}
        response_location['lat'] = u"%s"%sl.latitude
        response_location['lng'] = u"%s"%sl.longitude
        response_location['address'] = u"%s<br>%s"%(sl.address_street, sl.address_city)
        response_location['enc'] = u"%s"%(sl.enc_level)
        response_location['AP_no'] = u"%s"%(sl.AP_no)
        response_location['inst'] = sl.institutionid.org_name.get(lang='en').name
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



def servers(request):
    user = request.user
    servers = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
    if inst:
        servers = InstServer.objects.filter(instid=inst)
    return render_to_response('edumanage/servers.html', { 'servers': servers},
                                  context_instance=RequestContext(request, base_response(request)))



@login_required
def adduser(request):
    if request.method == "GET":
        form = ContactForm()
        return render_to_response('edumanage/add_user.html', { 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        form = ContactForm(request_data)
        if form.is_valid():
            contact = form.save()
            response_data = {}
            response_data['value'] = "%s" %contact.pk
            response_data['text'] = "%s" %contact
            return HttpResponse(json.dumps(response_data), mimetype='application/json')
        else:
            return render_to_response('edumanage/add_user.html', {'form': form,},
                                      context_instance=RequestContext(request, base_response(request)))

@login_required
def add_server(request, server_pk):
    user = request.user
    server = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False

    if request.method == "GET":

        # Determine add or edit
        try:         
            server = InstServer.objects.get(instid=inst, pk=server_pk)
            form = InstServerForm(instance=server)
        except InstServer.DoesNotExist:
            form = InstServerForm()
        form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        
        return render_to_response('edumanage/servers_edit.html', { 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            server = InstServer.objects.get(instid=inst, pk=server_pk)
            form = InstServerForm(request_data, instance=server)
        except InstServer.DoesNotExist:
            form = InstServerForm(request_data)
        
        if form.is_valid():
            instserverf = form.save()
            return HttpResponseRedirect(reverse("servers"))
        else:
            form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        print form.errors
        return render_to_response('edumanage/servers_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
def base_response(request):
    user = request.user
    inst = []
    server = []
    services = []
    try:
        profile = user.get_profile()
        institution = profile.institution
        inst.append(institution)
        server = InstServer.objects.filter(instid=institution)
        services = ServiceLoc.objects.filter(institutionid=institution)
    except UserProfile.DoesNotExist:
        pass
        
    return { 
            'inst_num': len(inst),
            'servers_num': len(server),
            'services_num': len(services),
            
        }

def geolocate(request):
    return render_to_response('front/geolocate.html',
                                  context_instance=RequestContext(request))


def closest(request):
    if request.method == 'GET':
        locs = []
        request_data = request.GET.copy()
        response_location = {}
        response_location["lat"] = request_data['lat']
        response_location["lng"] = request_data['lng']
        lat = float(request_data['lat'])
        lng = float(request_data['lng'])
        R = 6371
        distances = {}
        closestMarker = {}
        closest = -1
        doc = ET.parse(settings.KML_FILE)
        root = doc.getroot()
        r = root.getchildren()[0]
        for (counter, i) in enumerate(r.getchildren()):
            if "id" in i.keys():
                j = i.getchildren()
                pointname = j[0].text
                point = j[2].getchildren()[0].text
                pointlng, pointlat, pointele = point.split(',')
                dLat = rad(float(pointlat)-float(lat))
                dLong = rad(float(pointlng)-float(lng))
                a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(rad(lat)) * math.cos(rad(float(pointlat))) * math.sin(dLong/2) * math.sin(dLong/2) 
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                d = R * c
                distances[counter] = d
                if (closest == -1 or d < distances[closest]):
                    closest = counter
                    closestMarker = {"name": pointname, "lat": pointlat, "lng": pointlng, "text": j[1].text}
        return HttpResponse(json.dumps(closestMarker), mimetype='application/json')
        
        

def rad(x):
    return x*math.pi/180