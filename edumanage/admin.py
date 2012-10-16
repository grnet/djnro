# -*- coding: utf-8 -*-.
from django.contrib import admin
from eduroam.edumanage.models import *

from django.contrib.contenttypes import generic


class NameInline(generic.GenericTabularInline):
    model = Name_i18n
    
class UrlInline(generic.GenericTabularInline):
    model = URL_i18n


class InstitutionAdmin(admin.ModelAdmin):
    inlines = [
        NameInline,
    ]

class ServiceLocAdmin(admin.ModelAdmin):
    inlines = [
        NameInline,
    ]

class RealmInLine(admin.ModelAdmin):
    inlines = [
        UrlInline,
    ]

   
admin.site.register(Name_i18n)
admin.site.register(Contact)
admin.site.register(InstitutionContactPool)
admin.site.register(URL_i18n)
admin.site.register(InstRealm)
admin.site.register(InstServer)
admin.site.register(InstRealmMon)
admin.site.register(MonProxybackClient)
admin.site.register(MonLocalEAPOLData)
admin.site.register(ServiceLoc, ServiceLocAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(InstitutionDetails)
admin.site.register(Realm, RealmInLine)
admin.site.register(RealmData)