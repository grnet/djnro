# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from edumanage.models import *


def index(request):
    return render_to_response('base.html', context_instance=RequestContext(request))

@login_required
def manage(request):
    services_list = []
    servers_list = []
    inst_dets = Institution.objects.all()
    for inst in inst_dets:
        services = ServiceLoc.objects.filter(institutionid=inst)
        services_list.extend([s for s in services])
    for inst in inst_dets:
        servers = InstServer.objects.filter(instid=inst)
        servers_list.extend([s for s in servers])
    return render_to_response('edumanage/welcome.html', 
                              {
                               'institutions': inst_dets, 
                               'services': services_list,
                               'servers': servers_list
                               },  
                              context_instance=RequestContext(request))

@login_required
def institutions(request):
    user = request.user
    return render_to_response('edumanage/institutions.html', 
                              {
                               'institutions': inst_dets, 
                               'services': services_list,
                               'servers': servers_list
                               },  
                              context_instance=RequestContext(request))