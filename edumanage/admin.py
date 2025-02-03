# -*- coding: utf-8 -*-.
from django.contrib import admin
from edumanage.models import (
    Name_i18n,
    URL_i18n,
    Address_i18n,
    Contact,
    InstitutionContactPool,
    InstRealm,
    InstServer,
    InstRealmMon,
    MonProxybackClient,
    MonLocalAuthnParam,
    ServiceLoc,
    Institution,
    InstitutionDetails,
    Realm,
    RealmData,
    RealmServer,
    CatEnrollment
)
from edumanage.forms import (
    ServiceLocForm,
    ServiceLocURL_i18nForm,
    RealmName_i18nFormSet,
    InstitutionName_i18nFormSet,
    ServiceLocName_i18nFormSet,
    RealmAddress_i18nFormSet,
    InstitutionAddress_i18nFormSet,
    ServiceLocAddress_i18nFormSet,
    RealmURL_i18nFormSet,
    InstitutionURL_i18nFormSet,
    RealmServerForm,
)

from django.contrib.contenttypes import admin as contenttype_admin


class VenueInfoFilter(admin.SimpleListFilter):
    title = 'venue info'
    parameter_name = 'venue_info'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        vis = qs.order_by('venue_info').values_list('venue_info', flat=True).distinct()
        display = qs.model._meta.get_field('venue_info').flatchoices
        for vi in vis:
            title = [title for lookup, title in display if lookup == vi]
            if title:
                yield (vi, title[0])
            else:
                yield (vi, vi)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(venue_info=self.value())
        return queryset


class GenericTabularInlineValidateMin(contenttype_admin.GenericTabularInline):
    def get_formset(self, *args, **kwargs): # pylint: disable=arguments-differ
        if hasattr(self, 'validate_min'):
            kwargs['validate_min'] = self.validate_min # pylint: disable=no-member
        return super(GenericTabularInlineValidateMin, self).get_formset(
            *args, **kwargs)

class NameInline(GenericTabularInlineValidateMin):
    model = Name_i18n

class RealmNameInline(NameInline):
    formset = RealmName_i18nFormSet
    min_num = 1
    validate_min = True

class InstitutionNameInline(RealmNameInline):
    formset = InstitutionName_i18nFormSet

class ServiceLocNameInline(NameInline):
    formset = ServiceLocName_i18nFormSet

class UrlInline(GenericTabularInlineValidateMin):
    model = URL_i18n

class RealmUrlInline(UrlInline):
    formset = RealmURL_i18nFormSet
    min_num = 2
    validate_min = True

class InstitutionDetailsUrlInline(RealmUrlInline):
    formset = InstitutionURL_i18nFormSet

class ServiceLocUrlInline(UrlInline):
    form = ServiceLocURL_i18nForm

class AddressInline(GenericTabularInlineValidateMin):
    model = Address_i18n

class RealmAddressInline(AddressInline):
    formset = RealmAddress_i18nFormSet
    min_num = 1
    validate_min = True

class InstitutionDetailsAddressInline(RealmAddressInline):
    formset = InstitutionAddress_i18nFormSet

class ServiceLocAddressInline(AddressInline):
    formset = ServiceLocAddress_i18nFormSet


class InstitutionAdmin(admin.ModelAdmin):
    inlines = [
        InstitutionNameInline,
    ]
    list_filter = ('ertype',)
    readonly_fields = ('instid',)


class InstitutionDetailsAdmin(admin.ModelAdmin):
    inlines = [
        InstitutionDetailsAddressInline, InstitutionDetailsUrlInline,
    ]
    list_filter = ('institution__ertype', VenueInfoFilter)


class ServiceLocAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'institutionid')
    inlines = [
        ServiceLocUrlInline, ServiceLocNameInline, ServiceLocAddressInline,
    ]
    list_filter = ('SSID', 'enc_level', 'tag', VenueInfoFilter)
    form = ServiceLocForm
    readonly_fields = ('locationid',)


class RealmServerInline(admin.TabularInline):
    model = RealmServer
    form = RealmServerForm

class RealmServerAdmin(admin.ModelAdmin):
    form = RealmServerForm


class RealmInLine(admin.ModelAdmin):
    inlines = [
        RealmUrlInline, RealmNameInline, RealmAddressInline, RealmServerInline
    ]


class InstRealmAdmin(admin.ModelAdmin):
    list_display = ('realm', 'instid')
    list_filter = ('instid__ertype',)


class InstServerAdmin(admin.ModelAdmin):
    list_filter = ('ertype',)


class InstRealmMonAdmin(admin.ModelAdmin):
    list_filter = ('mon_type',)


class MonLocalAuthnParamAdmin(admin.ModelAdmin):
    list_filter = ('eap_method', 'phase2')


class CatEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cat_active')
    list_filter = ('cat_instance',)

admin.site.register(Name_i18n)
admin.site.register(Address_i18n)
admin.site.register(Contact)
admin.site.register(InstitutionContactPool)
admin.site.register(URL_i18n)
admin.site.register(InstRealm, InstRealmAdmin)
admin.site.register(InstServer, InstServerAdmin)
admin.site.register(InstRealmMon, InstRealmMonAdmin)
admin.site.register(MonProxybackClient)
admin.site.register(MonLocalAuthnParam, MonLocalAuthnParamAdmin)
admin.site.register(ServiceLoc, ServiceLocAdmin)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(InstitutionDetails, InstitutionDetailsAdmin)
admin.site.register(Realm, RealmInLine)
admin.site.register(RealmServer, RealmServerAdmin)
admin.site.register(RealmData)
admin.site.register(CatEnrollment, CatEnrollmentAdmin)

from django import forms
from django.core.urlresolvers import reverse
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from tinymce.widgets import TinyMCE

class TinyMCEFlatPageAdmin(FlatPageAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'content':
            return db_field.formfield(widget=TinyMCE(
                attrs={'cols': 80, 'rows': 30},
                mce_attrs={'external_link_list_url': reverse('tinymce-linklist')},
            ))
        return super(TinyMCEFlatPageAdmin, self).formfield_for_dbfield(db_field, **kwargs)

from django.contrib import admin

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, TinyMCEFlatPageAdmin)
