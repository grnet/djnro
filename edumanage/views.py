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
from xml.etree import ElementTree as ET

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
            UrlFormSet = generic_inlineformset_factory(URL_i18n, extra=2, formset=UrlFormSetFactInst, can_delete=True)
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
            try:
                profile = user.get_profile()
                inst = profile.institution
            except UserProfile.DoesNotExist:
                inst = False
            form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
            return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form, 'urls_form': urls_form},
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
        form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
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
            form.fields['contact'] = forms.ModelMultipleChoiceField(queryset=Contact.objects.filter(pk__in=getInstContacts(inst)))
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
    user = request.user
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
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
        return render_to_response('edumanage/servers_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
def realms(request):
    user = request.user
    servers = False
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
    if inst:
        realms = InstRealm.objects.filter(instid=inst)
    return render_to_response('edumanage/realms.html', { 'realms': realms},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
def add_realm(request, realm_pk):
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
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm()
        form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
        form.fields['proxyto'] = forms.ModelMultipleChoiceField(queryset=InstServer.objects.filter(pk__in=getInstServers(inst)))
        return render_to_response('edumanage/realms_edit.html', { 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            realm = InstRealm.objects.get(instid=inst, pk=realm_pk)
            form = InstRealmForm(request_data, instance=realm)
        except InstRealm.DoesNotExist:
            form = InstRealmForm(request_data)
        
        if form.is_valid():
            instserverf = form.save()
            return HttpResponseRedirect(reverse("realms"))
        else:
            form.fields['instid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)
            form.fields['proxyto'] = forms.ModelMultipleChoiceField(queryset=InstServer.objects.filter(pk__in=getInstServers(inst)))
        return render_to_response('edumanage/realms_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
def del_realm(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        realm_pk = req_data['realm_pk']
        profile = user.get_profile()
        institution = profile.institution
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
def contacts(request):
    user = request.user
    servers = False
    instcontacts = []
    try:
        profile = user.get_profile()
        inst = profile.institution
    except UserProfile.DoesNotExist:
        inst = False
    if inst:
        instcontacts.extend([x.contact.pk for x in InstitutionContactPool.objects.filter(institution=inst)])
        print instcontacts
        contacts = Contact.objects.filter(pk__in=instcontacts)
        print contacts
    return render_to_response('edumanage/contacts.html', { 'contacts': contacts},
                                  context_instance=RequestContext(request, base_response(request)))

@login_required
def add_contact(request, contact_pk):
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
            contactinst = InstitutionContactPool.objects.get(institution=inst, contact__pk=contact_pk)
            contact = contactinst.contact
            form = ContactForm(instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm()

        return render_to_response('edumanage/contacts_edit.html', { 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            contactinst = InstitutionContactPool.objects.get(institution=inst, contact__pk=contact_pk)
            contact = contactinst.contact
            form = ContactForm(request_data, instance=contact)
        except InstitutionContactPool.DoesNotExist:
            form = ContactForm(request_data)
        
        if form.is_valid():
            contact = form.save()
            instContPool, created = InstitutionContactPool.objects.get_or_create(contact=contact, institution=inst)
            instContPool.save()
            return HttpResponseRedirect(reverse("contacts"))
        return render_to_response('edumanage/contacts_edit.html', { 'form': form},
                                  context_instance=RequestContext(request, base_response(request)))


@login_required
def del_contact(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        contact_pk = req_data['contact_pk']
        profile = user.get_profile()
        institution = profile.institution
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
def base_response(request):
    user = request.user
    inst = []
    server = []
    services = []
    instrealms = []
    instcontacts = []
    contacts = []
    try:
        profile = user.get_profile()
        institution = profile.institution
        inst.append(institution)
        server = InstServer.objects.filter(instid=institution)
        services = ServiceLoc.objects.filter(institutionid=institution)
        instrealms = InstRealm.objects.filter(instid=institution)
        instcontacts.extend([x.contact.pk for x in InstitutionContactPool.objects.filter(institution=institution)])
        contacts = Contact.objects.filter(pk__in=instcontacts)
    except UserProfile.DoesNotExist:
        pass
        
    return { 
            'inst_num': len(inst),
            'servers_num': len(server),
            'services_num': len(services),
            'realms_num': len(instrealms),
            'contacts_num': len(contacts),
            
        }

@login_required
def del_server(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        server_pk = req_data['server_pk']
        profile = user.get_profile()
        institution = profile.institution
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
def del_service(request):
    if request.method == 'GET':
        user = request.user
        req_data = request.GET.copy()
        service_pk = req_data['service_pk']
        profile = user.get_profile()
        institution = profile.institution
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
        

def instxml(request):
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("institutions")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "institutions.xsd")
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
        instType.text = "%s" %inst.ertype
        
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
            instContactName.text = "%s %s" %(contact.firstname, contact.lastname)
            
            instContactEmail = ET.SubElement(instContact, "email")
            instContactEmail.text = contact.email
            
            instContactPhone = ET.SubElement(instContact, "phone")
            instContactPhone.text = contact.phone
        
        for url in inst.url.all():
            instUrl = ET.SubElement(instElement, "%s_URL"%(url.urltype))
            instUrl.attrib["lang"] = url.lang
            instUrl.text = url.url
        
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
            
            instLocSSID = ET.SubElement(instLocation, "SSID")
            instLocSSID.text = serviceloc.SSID
            
            instLocEncLevel = ET.SubElement(instLocation, "enc_level")
            instLocEncLevel.text = serviceloc.enc_level
            
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

        instTs = ET.SubElement(instElement, "ts")
        instTs.text = "%s" %inst.ts.isoformat()
            
    return render_to_response("general/institution.xml", {"xml":to_xml(root)},context_instance=RequestContext(request,), mimetype="application/xml")
        

def realmxml(request):
    realm = Realm.objects.all()[0]
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("realms")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "realm.xsd")
    #root.attrib["xsi:noNamespaceSchemaLocation"] = "institution.xsd"
    realmElement = ET.SubElement(root, "realm")
    
    realmCountry = ET.SubElement(realmElement, "country")
    realmCountry.text = realm.country
        
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
        realmContactName.text = "%s %s" %(contact.firstname, contact.lastname)
        
        realmContactEmail = ET.SubElement(realmContact, "email")
        realmContactEmail.text = contact.email
        
        realmContactPhone = ET.SubElement(realmContact, "phone")
        realmContactPhone.text = contact.phone
    
    for url in realm.url.all():
        realmUrl = ET.SubElement(realmElement, "%s_URL"%(url.urltype))
        realmUrl.attrib["lang"] = url.lang
        realmUrl.text = url.url
    
    return render_to_response("general/realm.xml", {"xml":to_xml(root)},context_instance=RequestContext(request,), mimetype="application/xml")

def realmdataxml(request):
    realm = Realm.objects.all()[0]
    ET._namespace_map["http://www.w3.org/2001/XMLSchema-instance"] = 'xsi'
    root = ET.Element("realm-data")
    NS_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    root.set(NS_XSI + "noNamespaceSchemaLocation", "realm-data.xsd")
    
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
