# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from edumanage.models import *
from edumanage.forms import *
from django import forms

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
    if request.method == "GET":
        try:
            profile = user.get_profile()
            inst = profile.institution
        except UserProfile.DoesNotExist:
            inst = False
            
        if (not inst) or (int(inst.pk) != int(institution_pk)):
#            messages.add_message(request, messages.WARNING,
#                             _("Insufficient rights on Institution. Contact your administrator"))
            return HttpResponseRedirect(reverse("institution"))         

        form = InstDetailsForm()
        form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
        return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request))
    elif request.method == 'POST':
        request_data = request.POST.copy()
        form = InstDetailsForm(request_data)
        if form.is_valid():
            instdets = form.save(commit=False)
            instdets.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse("institution"))
        else:
            try:
                profile = user.get_profile()
                inst = profile.institution
            except UserProfile.DoesNotExist:
                inst = False
                form.fields['institution'] = forms.ModelChoiceField(queryset=Institution.objects.filter(pk=institution_pk), empty_label=None)
            return render_to_response('edumanage/institution_edit.html', { 'institution': inst, 'form': form},
                                  context_instance=RequestContext(request))

