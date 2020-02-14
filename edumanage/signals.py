# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from edumanage.models import ServiceLoc, Coordinates
from edumanage.views import ourPoints

@receiver([post_save, post_delete], sender=ServiceLoc,
              dispatch_uid="edumanage.views.ourpoints.recache")
def recache_ourpoints(sender, instance, **kwargs):
    if isinstance(instance, ServiceLoc):
        inst = instance.institutionid
    else:
        inst = None

    ourPoints(institution=inst, cache_flush=True)

@receiver(post_save, sender=ServiceLoc,
          dispatch_uid="edumanage.models.ServiceLoc.save_latlon_cache")
def save_latlon_cache(sender, instance, **kwargs):
    if not isinstance(instance, ServiceLoc):
        return
    try:
        props = {
            p: instance.__dict__[p] for p in ['latitude', 'longitude']
        }
    except KeyError:
        return
    if not all([props[p] is not None for p in props]):
        return
    try:
        instance.coordinates.update_or_create(defaults=props)
    except Coordinates.MultipleObjectsReturned:
        # following receiver ensures this should never happen, but anyway
        instance.coordinates.filter(
            id=instance.coordinates.first().id
        ).update(**props)
    for p in props:
        instance.__dict__.pop(p)


@receiver(m2m_changed, sender=ServiceLoc.coordinates.through,
          dispatch_uid="edumanage.models.ServiceLoc.coordinates.enforce_one")
def sloc_coordinates_enforce_one(sender, instance, **kwargs):
    action = kwargs['action']
    reverse = kwargs['reverse']
    pk_set = kwargs['pk_set']
    if action != 'pre_add':
        return
    if len(pk_set) > 1:
        invalid = True
    else:
        if not reverse:
            # through (sender) objects having FK to instance (ServiceLoc)
            sloc_coords = sender.objects.filter(serviceloc=instance)
        else:
            pk = next(iter(pk_set))
            # through (sender) objects having FK to ServiceLoc (pk added)
            sloc_coords = sender.objects.filter(serviceloc__pk=pk)
        invalid = sloc_coords.count() > 0
    if invalid:
        raise ValidationError(
            {'coordinates': _(
                'Only one set of coordinates per ServiceLoc is allowed'
            )}
        )
