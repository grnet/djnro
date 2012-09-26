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

def index(request):
    return render_to_response('base.html', context_instance=RequestContext(request))

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
                              context_instance=RequestContext(request))

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
                              context_instance=RequestContext(request))



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
                                  context_instance=RequestContext(request))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        try:         
            inst_details = InstitutionDetails.objects.get(institution=inst)
            form = InstDetailsForm(request_data, instance=inst_details)
        except InstitutionDetails.DoesNotExist:
            form = InstDetailsForm(request_data)
        if form.is_valid():
            instdets = form.save()
            print "SAVED M2M"
            return HttpResponseRedirect(reverse("institutions"))
        else:
            try:
                profile = user.get_profile()
                inst = profile.institution
            except UserProfile.DoesNotExist:
                inst = False
                form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request))


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
                              context_instance=RequestContext(request))



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
        
        NameFormSet = generic_inlineformset_factory(Name_i18n, extra=2)
        names_form = NameFormSet()
        if (service):
            NameFormSet = generic_inlineformset_factory(Name_i18n, extra=0, formset=NameFormSetFact)
            names_form = NameFormSet(instance=service)
        return render_to_response('edumanage/services_edit.html', { 'form': form, 'services_form':names_form},
                                  context_instance=RequestContext(request))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        NameFormSet = generic_inlineformset_factory(Name_i18n, extra=0, formset=NameFormSetFact)
        try:         
            service = ServiceLoc.objects.get(institutionid=inst, pk=service_pk)
            form = ServiceLocForm(request_data, instance=service)
            print "OKOK"
            names_form = NameFormSet(request_data, instance=service)
        except ServiceLoc.DoesNotExist:
            form = ServiceLocForm(request_data)
            names_form = NameFormSet(request_data)
        
        if form.is_valid() and names_form.is_valid():
            serviceloc = form.save()
            

            for nform in names_form.forms:
                names = nform.save(commit=False)
                names.content_object = serviceloc
                names.save()
            return HttpResponseRedirect(reverse("services"))
        else:
            form.fields['institutionid'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=inst.pk), empty_label=None)

        return render_to_response('edumanage/services_edit.html', { 'institution': inst, 'form': form, 'services_form':names_form},
                                  context_instance=RequestContext(request))


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
            response_location['name'] = sl.loc_name.get(lang='en').name
            response_location['key'] = u"%s"%sl.pk
            locs.append(response_location)
        return HttpResponse(json.dumps(locs), mimetype='application/json')
    else:
       return HttpResponseNotFound('<h1>Something went really wrong</h1>')
