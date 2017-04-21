# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from edumanage.models import ServiceLoc
from edumanage.views import ourPoints

@receiver([post_save, post_delete], sender=ServiceLoc,
              dispatch_uid="edumanage.views.ourpoints.recache")
def recache_ourpoints(sender, instance, **kwargs):
    if isinstance(instance, ServiceLoc):
        inst = instance.institutionid
    else:
        inst = None

    ourPoints(institution=inst, cache_flush=True)
