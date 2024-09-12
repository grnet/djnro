# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from collections import defaultdict
from django.db.models.signals import (
    post_save, pre_delete, post_delete, m2m_changed
)
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from edumanage.models import ServiceLoc, Coordinates, RealmServer
from edumanage.views import ourPoints

class disable_signals(object): # pylint: disable=invalid-name
    def __init__(self, *signals_dispatch_uids):
        self.signals = signals_dispatch_uids
        self.stashed_receivers = defaultdict(list)

    def __enter__(self):
        for signal, dispatch_uids in self.signals:
            if not isinstance(dispatch_uids, (tuple, list)):
                dispatch_uids = [dispatch_uids]
            for dispatch_uid in dispatch_uids:
                for idx, rcvr in enumerate(list(signal.receivers)):
                    (signal_dispatch_uid, __), __ = rcvr
                    if signal_dispatch_uid == dispatch_uid:
                        self.stashed_receivers[signal].append(rcvr)
                        del signal.receivers[idx]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in self.stashed_receivers:
            for rcvr in self.stashed_receivers[signal]:
                signal.receivers.append(rcvr)


@receiver(pre_delete, sender=ServiceLoc,
          dispatch_uid="edumanage.models.ServiceLoc.clean_orphan_coordinates")
def clean_serviceloc_coordinates(sender, instance, **kwargs):
    instance.coordinates.all().delete()

DUID_RECACHE_OURPOINTS = "edumanage.views.ourpoints.recache"

@receiver([post_save, post_delete], sender=ServiceLoc,
          dispatch_uid=DUID_RECACHE_OURPOINTS)
def recache_ourpoints(sender, instance, **kwargs):
    if isinstance(instance, ServiceLoc):
        inst = instance.institutionid
    else:
        inst = None

    ourPoints(institution=inst, cache_flush=True)


DUID_SAVE_SERVICELOC_LATLON_CACHE = \
    "edumanage.models.ServiceLoc.save_latlon_cache"

@receiver(post_save, sender=ServiceLoc,
          dispatch_uid=DUID_SAVE_SERVICELOC_LATLON_CACHE)
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
          dispatch_uid="edumanage.models.Coordinates.serviceloc_set.enforce_one")
def coords_serviceloc_enforce_one(sender, instance, **kwargs):
    action = kwargs['action']
    reverse = kwargs['reverse']
    pk_set = kwargs['pk_set']
    if action != 'pre_add':
        return
    if len(pk_set) > 1:
        invalid = True
    else:
        # pk = next(iter(pk_set))
        if not reverse:
            pk = next(iter(pk_set))
            # through (sender) objects having FK to Coordinates (pk added)
            coord_slocs = sender.objects.filter(coordinates__id=pk)
        else:
            # through (sender) objects having FK to instance (Coordinates)
            coord_slocs = sender.objects.filter(coordinates=instance)
        invalid = coord_slocs.count() > 0
    if invalid:
        raise ValidationError(
            {'serviceloc': _(
                'Coordinates may not be linked to more than one ServiceLoc'
            )}
        )


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

# Update Realm TS whenever a RealmServer is added/changed/deleted
@receiver((post_save, post_delete), sender=RealmServer,
          dispatch_uid="edumanage.models.RealmServer.update_realm_ts")
def realmserver_update_realm_ts(sender, instance, **kwargs):
    instance.realm.save()
