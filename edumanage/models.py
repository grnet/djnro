# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.text import capfirst
from django.core import exceptions
from django.conf import settings
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError


class MultiSelectFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        self.max_choices = 4
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        # if value and self.max_choices and len(value) > self.max_choices:
        #     raise forms.ValidationError('You must select a maximum of %s choice%s.'
        #             % (apnumber(self.max_choices), pluralize(self.max_choices)))
        return value


class MultiSelectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_choices_default(self):
        return self.get_choices(include_blank=False)

    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        choicedict = dict(field.choices)

    def formfield(self, **kwargs):
        # don't call super, as that overrides default widget if it has choices
        defaults = {
            'required': not self.blank,
            'label': capfirst(self.verbose_name),
            'help_text': self.help_text,
            'choices': self.choices
        }
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectFormField(**defaults)

    def get_prep_value(self, value):
        return value

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return ",".join(value)

    def to_python(self, value):
        if value is not None:
            return value if isinstance(value, list) else value.split(',')
        return ''

    def contribute_to_class(self, cls, name):
        super(MultiSelectField, self).contribute_to_class(cls, name)
        if self.choices:
            func = lambda self, fieldname = name, choicedict = dict(self.choices): ",".join([choicedict.get(value, value) for value in getattr(self, fieldname)])
            setattr(cls, 'get_%s_display' % self.name, func)

    def validate(self, value, model_instance):
        arr_choices = self.get_choices_selected(self.get_choices_default())
        for opt_select in value:
            if (opt_select not in arr_choices):  # the int() here is for comparing with integer choices
                raise exceptions.ValidationError(self.error_messages['invalid_choice'] % value)
        return

    def get_choices_selected(self, arr_choices=''):
        if not arr_choices:
            return False
        list = []
        for choice_selected in arr_choices:
            list.append(choice_selected[0])
        return list

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

# needed for South compatibility

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^edumanage\.models\.MultiSelectField"])

ERTYPES = (
    (1, 'IdP only'),
    (2, 'SP only'),
    (3, 'IdP and SP'),
)

RADPROTOS = (
    ('radius', 'traditional RADIUS over UDP'),
#        ('radius-tcp', 'RADIUS over TCP (RFC6613)'),
#        ('radius-tls', 'RADIUS over TLS (RFC6614)'),
#        ('radius-dtls', 'RADIUS over datagram TLS (RESERVED)'),
)


ADDRTYPES = (
    ('any', 'Default'),
    ('ipv4', 'IPv4 only'),
    #('ipv6', 'IPv6 only'), # Commented for the time...not yet in use
)

RADTYPES = (
    ('auth', 'Handles Access-Request packets only'),
    ('acct', 'Handles Accounting-Request packets only'),
    ('auth+acct', 'Handles both Access-Request and Accounting-Request packets'),
)


class Name_i18n(models.Model):
    '''
    Name in a particular language
    '''

    name = models.CharField(max_length=80)
    lang = models.CharField(max_length=5, choices=settings.URL_NAME_LANGS)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Name (i18n)"
        verbose_name_plural = "Names (i18n)"


class Contact(models.Model):
    '''
    Contact
    '''

    name = models.CharField(max_length=255, db_column='contact_name')
    email = models.CharField(max_length=80, db_column='contact_email')
    phone = models.CharField(max_length=80, db_column='contact_phone')

    def __unicode__(self):
        return '%s <%s> (%s)' % (self.name, self.email, self.phone)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"


class InstitutionContactPool(models.Model):
    contact = models.OneToOneField(Contact)
    institution = models.ForeignKey("Institution")

    def __unicode__(self):
        return u"%s:%s" %(self.contact, self.institution)

    class Meta:
        verbose_name = "Instutution Contact (Pool)"
        verbose_name_plural = "Instutution Contacts (Pool)"


class URL_i18n(models.Model):
    '''
    URL of a particular type in a particular language
    '''

    URLTYPES = (
        ('info', 'Info'),
        ('policy', 'Policy'),
    )
    url = models.CharField(max_length=180, db_column='URL')
    lang = models.CharField(max_length=5, choices=settings.URL_NAME_LANGS)
    urltype = models.CharField(max_length=10, choices=URLTYPES, db_column='type')
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Url (i18n)"
        verbose_name_plural = "Urls (i18n)"

    def __unicode__(self):
        return self.url


class InstRealm(models.Model):
    '''
    Realm of an IdP Institution
    '''
    # accept if instid.ertype: 1 (idp) or 3 (idpsp)
    realm = models.CharField(max_length=160)
    instid = models.ForeignKey("Institution", verbose_name="Institution")
    proxyto = models.ManyToManyField("InstServer", help_text=_("Only IdP and IdP/SP server types are allowed"))

    class Meta:
        verbose_name = "Institution Realm"
        verbose_name_plural = "Institutions' Realms"

    def __unicode__(self):
        return '%s' % self.realm

    def get_servers(self):
        return ",".join(["%s" % x for x in self.proxyto.all()])


class InstServer(models.Model):
    '''
    Server of an Institution
    '''
    instid = models.ForeignKey("Institution")
    ertype = models.PositiveIntegerField(max_length=1, choices=ERTYPES, db_column='type')
    # ertype:
    # 1: accept if instid.ertype: 1 (idp) or 3 (idpsp)
    # 2: accept if instid.ertype: 2 (sp) or 3 (idpsp)
    # 3: accept if instid.ertype: 3 (idpsp)

    # hostname/ipaddr or descriptive label of server
    name = models.CharField(max_length=80, help_text=_("Descriptive label"), null=True, blank=True) # ** (acts like a label)
    # hostname/ipaddr of server, overrides name
    addr_type = models.CharField(max_length=16, choices=ADDRTYPES, default='ipv4')
    host = models.CharField(max_length=80, help_text=_("IP address | FQDN hostname")) # Handling with FQDN parser or ipaddr (google lib) * !!! Add help text to render it in template (mandatory, unique)
    #TODO: Add description field or label field
    # accept if type: 1 (idp) or 3 (idpsp) (for the folowing 4 fields)
    rad_pkt_type = models.CharField(max_length=48, choices=RADTYPES, default='auth+acct', null=True, blank=True,)
    auth_port = models.PositiveIntegerField(max_length=5, null=True, blank=True, default=1812, help_text=_("Default for RADIUS: 1812")) # TODO: Also ignore while exporting XML
    acct_port = models.PositiveIntegerField(max_length=5, null=True, blank=True, default=1813, help_text=_("Default for RADIUS: 1813"))
    status_server = models.BooleanField(help_text=_("Do you accept Status-Server requests?"))

    secret = models.CharField(max_length=80)
    proto = models.CharField(max_length=12, choices=RADPROTOS, default='radius')
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institution Server"
        verbose_name_plural = "Institutions' Servers"

    def __unicode__(self):
        return _('Server: %(servername)s, Type: %(ertype)s') % {
            # but name is many-to-many from institution
            # 'inst': self.instid,
            'servername': self.get_name(),
            # the human-readable name would be nice here
            'ertype': self.get_ertype_display(),
        }

    def get_name(self):
        if self.name:
            return self.name
        return self.host

    # If a server is a proxy for a realm, can not change type to SP
    def clean(self):
        if self.ertype == 2:
            realms = InstRealm.objects.filter(proxyto=self)
            if len(realms) > 0:
                text = str()
                for realm in realms:
                    text = text + ' ' + realm.realm
                raise ValidationError(
                    'You cannot change this server to SP (it is used by realms %s)' %
                    ', '.join([r.realm for r in realms])
                    )


class InstRealmMon(models.Model):
    '''
    Realm of an IdP Institution to be monitored
    '''

    MONTYPES = (
        ('localauthn', 'Institution provides account for the NRO to monitor the realm' ),
        # ('loopback', 'Institution proxies the realm back to the NRO'),
    )

    realm = models.ForeignKey(InstRealm)
    mon_type = models.CharField(max_length=16, choices=MONTYPES)

    class Meta:
        unique_together = ('realm', 'mon_type')
        verbose_name = "Institution Monitored Realm"
        verbose_name_plural = "Institution Monitored Realms"

    def __unicode__(self):
        return "%s-%s" % (self.realm.realm, self.mon_type)
#    def __unicode__(self):
#        return _('Institution: %(inst)s, Monitored Realm: %(monrealm)s, Monitoring Type: %(montype)s') % {
#        # but name is many-to-many from institution
#            'inst': self.instid.name,
#            'monrealm': self.realm,
#            'montype': self.mon_type,
#            }


class MonProxybackClient(models.Model):
    '''
    Server of an Institution that will be proxying back requests for a monitored realm
    '''

    instrealmmonid = models.ForeignKey("InstRealmMon")
    # hostname/ipaddr or descriptive label of server
    name = models.CharField(
        max_length=80,
        help_text=_("Descriptive label"),
        null=True,
        blank=True
    )  # ** (acts like a label)
    # hostname/ipaddr of server, overrides name
    host = models.CharField(
        max_length=80,
        help_text=_("IP address | FQDN hostname")
    )  # Handling with FQDN parser or ipaddr (google lib) * !!! Add help text to render it in template (mandatory, unique)
    status_server = models.BooleanField()
    secret = models.CharField(max_length=80)
    proto = models.CharField(max_length=12, choices=RADPROTOS)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institution Proxyback Client"
        verbose_name_plural = "Institution Proxyback Clients"

    def __unicode__(self):
        return _('Monitored Realm: %(monrealm)s, Proxyback Client: %(servername)s') % {
            # but name is many-to-many from institution
            'monrealm': self.instrealmmonid.realm,
            'servername': self.name,
        }


class MonLocalAuthnParam(models.Model):
    '''
    Parameters for an old-style monitored realm
    '''

    EAPTYPES = (
        ('PEAP', 'EAP-PEAP'),
        ('TTLS', 'EAP-TTLS'),
        # ('TLS', 'EAP-TLS'),
    )
    EAP2TYPES = (
        ('PAP', 'PAP'),
        ('CHAP', 'CHAP'),
        ('MS-CHAPv2', 'MS-CHAPv2'),
    )
#    MONRESPTYPES = (
#                ('accept', 'Access-Accept expected' ),
#                ('reject', 'Access-Reject expected'),
#                ('both', 'RESERVED'),
#               )

    instrealmmonid = models.OneToOneField("InstRealmMon")
    eap_method = models.CharField(max_length=16, choices=EAPTYPES)
    phase2 = models.CharField(max_length=16, choices=EAP2TYPES)
    # only local-part, no realm
    username = models.CharField(max_length=36)
    passwp = models.CharField(max_length=80, db_column='pass')
    # TODO: In next releast change it to TextField and add a key field
    # cert = models.CharField(max_length=32)
    # exp_response = models.CharField(max_length=6, choices=MONRESPTYPES)

    class Meta:
        verbose_name = "Monitored Realm (local authn)"
        verbose_name_plural = "Monitored Realms (local authn)"

    def __unicode__(self):
        return _('Monitored Realm: %(monrealm)s, EAP Method: %(eapmethod)s, Phase 2: %(phase2)s, Username: %(username)s') % {
            # but name is many-to-many from institution
            'monrealm': self.instrealmmonid.realm,
            'eapmethod': self.eap_method,
            'phase2': self.phase2,
            'username': self.username,
        }


class ServiceLoc(models.Model):
    '''
    Service Location of an SP/IdPSP Institution
    '''

    ENCTYPES = (
        ('WPA/TKIP', 'WPA-TKIP'),
        ('WPA/AES', 'WPA-AES'),
        ('WPA2/TKIP', 'WPA2-TKIP'),
        ('WPA2/AES', 'WPA2-AES'),
    )

    # accept if institutionid.ertype: 2 (sp) or 3 (idpsp)
    institutionid = models.ForeignKey("Institution", verbose_name="Institution")
    longitude = models.DecimalField(max_digits=12, decimal_places=8)
    latitude = models.DecimalField(max_digits=12, decimal_places=8)
    # TODO: multiple names can be specified [...] name in English is required
    loc_name = generic.GenericRelation(Name_i18n)
    address_street = models.CharField(max_length=96)
    address_city = models.CharField(max_length=64)
    contact = models.ManyToManyField(Contact, blank=True, null=True)
    SSID = models.CharField(max_length=16)
    enc_level = MultiSelectField(max_length=64, choices=ENCTYPES, blank=True, null=True)
    port_restrict = models.BooleanField()
    transp_proxy = models.BooleanField()
    IPv6 = models.BooleanField()
    NAT = models.BooleanField()
    AP_no = models.PositiveIntegerField(max_length=3)
    wired = models.BooleanField()
    # only urltype = 'info' should be accepted here
    url = generic.GenericRelation(URL_i18n, blank=True, null=True)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Location"
        verbose_name_plural = "Service Locations"

    def __unicode__(self):
        return _('Institution: %(inst)s, Service Location: %(locname)s') % {
            # but name is many-to-many from institution
            'inst': self.institutionid,
            # but locname is many-to-many
            'locname': self.get_name(),
        }

    def get_name(self, lang=None):
        name = ', '.join([i.name for i in self.loc_name.all()])
        if not lang:
            return name
        else:
            try:
                name = self.loc_name.get(lang=lang)
                return name
            except Exception:
                return name
    get_name.short_description = 'Location Name'


class Institution(models.Model):
    '''
    Institution
    '''

    realmid = models.ForeignKey("Realm")
    org_name = generic.GenericRelation(Name_i18n)
    ertype = models.PositiveIntegerField(max_length=1, choices=ERTYPES, db_column='type')

    def __unicode__(self):
        return "%s" % ', '.join([i.name for i in self.org_name.all()])

    def get_name(self, lang=None):
        name = ', '.join([i.name for i in self.org_name.all()])
        if not lang:
            return name
        else:
            try:
                name = self.org_name.get(lang=lang)
                return name
            except Exception:
                return name

    def get_active_cat_enrl(self):
        urls = []
        active_cat_enrl = self.catenrollment_set.filter(url='ACTIVE', cat_instance='production')
        for catenrl in active_cat_enrl:
            if catenrl.cat_configuration_url:
                urls.append(catenrl.cat_configuration_url)
        return urls


class InstitutionDetails(models.Model):
    '''
    Institution Details
    '''
    institution = models.OneToOneField(Institution)
    # TODO: multiple names can be specified [...] name in English is required
    address_street = models.CharField(max_length=96)
    address_city = models.CharField(max_length=64)
    contact = models.ManyToManyField(Contact)
    url = generic.GenericRelation(URL_i18n)
    # accept if ertype: 2 (sp) or 3 (idpsp) (Applies to the following field)
    oper_name = models.CharField(
        max_length=24,
        null=True,
        blank=True,
        help_text=_('The primary, registered domain name for your institution, eg. example.com.<br>This is used to derive the Operator-Name attribute according to RFC5580, par.4.1, using the REALM namespace.')
    )
    # accept if ertype: 1 (idp) or 3 (idpsp) (Applies to the following field)
    number_user = models.PositiveIntegerField(max_length=6, null=True, blank=True, help_text=_("Number of users (individuals) that are eligible to participate in eduroam service"))
    number_id = models.PositiveIntegerField(max_length=6, null=True, blank=True, help_text=_("Number of issued e-identities (credentials) that may be used for authentication in eduroam service"))
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institutions' Details"
        verbose_name_plural = "Institution Details"

    def __unicode__(self):
        return _('Institution: %(inst)s, Type: %(ertype)s') % {
            # but name is many-to-many from institution
            'inst': ', '.join([i.name for i in self.institution.org_name.all()]),
            'ertype': self.institution.get_ertype_display(),
        }

    def get_inst_name(self):
        return ", ".join([i.name for i in self.institution.org_name.all()])
    get_inst_name.short_description = "Institution Name"


class Realm(models.Model):
    '''
    Realm
    '''

    country = models.CharField(max_length=5, choices=settings.REALM_COUNTRIES)
    stype = models.PositiveIntegerField(max_length=1, default=0, editable=False)
    # TODO: multiple names can be specified [...] name in English is required
    org_name = generic.GenericRelation(Name_i18n)
    address_street = models.CharField(max_length=32)
    address_city = models.CharField(max_length=24)
    contact = models.ManyToManyField(Contact)
    url = generic.GenericRelation(URL_i18n)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Realm"
        verbose_name_plural = "Realms"

    def __unicode__(self):
        return _('Country: %(country)s, NRO: %(orgname)s') % {
            # but name is many-to-many from institution
            'orgname': ', '.join([i.name for i in self.org_name.all()]),
            'country': self.country,
        }


# TODO: this represents a *database view* "realm_data", find a better way to write it
class RealmData(models.Model):
    '''
    Realm statistics
    '''

    realmid = models.OneToOneField(Realm)
    # db: select count(institution.id) as number_inst from institution, realm where institution.realmid == realm.realmid
    number_inst = models.PositiveIntegerField(max_length=5, editable=False)
    # db: select sum(institution.number_user) as number_user from institution, realm where institution.realmid == realm.realmid
    number_user = models.PositiveIntegerField(max_length=9, editable=False)
    # db: select sum(institution.number_id) as number_id from institution, realm where institution.realmid == realm.realmid
    number_id = models.PositiveIntegerField(max_length=9, editable=False)
    # db: select count(institution.id) as number_IdP from institution, realm where institution.realmid == realm.realmid and institution.type == 1
    number_IdP = models.PositiveIntegerField(max_length=5, editable=False)
    # db: select count(institution.id) as number_SP from institution, realm where institution.realmid == realm.realmid and institution.type == 2
    number_SP = models.PositiveIntegerField(max_length=5, editable=False)
    # db: select count(institution.id) as number_IdPSP from institution, realm where institution.realmid == realm.realmid and institution.type == 3
    number_IdPSP = models.PositiveIntegerField(max_length=5, editable=False)
    # db: select greatest(max(realm.ts), max(institution.ts)) as ts from institution, realm where institution.realmid == realm.realmid
    ts = models.DateTimeField(editable=False)

    def __unicode__(self):
        return _('Country: %(country)s, NRO: %(orgname)s, Institutions: %(inst)s, IdPs: %(idp)s, SPs: %(sp)s, IdPSPs: %(idpsp)s, Users: %(numuser)s, Identities: %(numid)s') % {
            # but name is many-to-many from institution
            'orgname': self.org_name,
            'country': self.country,
            'inst': self.number_inst,
            'idp': self.number_IdP,
            'sp': self.number_SP,
            'idpsp': self.number_IdPSP,
            'numuser': self.number_user,
            'numid': self.number_id,
        }


class CatEnrollment(models.Model):
    ''' Eduroam CAT enrollment '''

    ACTIVE = u"ACTIVE"

    cat_inst_id = models.PositiveIntegerField(max_length=10)
    inst = models.ForeignKey(Institution)
    url = models.CharField(max_length=255, blank=True, null=True, help_text="Set to ACTIVE if institution has CAT profiles")
    cat_instance = models.CharField(max_length=50, choices=settings.CAT_INSTANCES)
    applier = models.ForeignKey(User)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['inst', 'cat_instance']

    def __unicode__(self):
        return "%s: %s" % (self.cat_inst_id, ', '.join([i.name for i in self.inst.org_name.all()]))

    def cat_active(self):
        return self.url == self.ACTIVE

    def cat_configuration_url(self):
        if self.cat_active():
            try:
                return "%s?idp=%s" % (settings.CAT_AUTH[self.cat_instance]['CAT_PROFILES_URL'],self.cat_inst_id)
            except:
                return False
        return False

    def cat_idpmgmt_url(self):
        if self.cat_active():
            try:
                return "%s?inst_id=%s" % (settings.CAT_AUTH[self.cat_instance]['CAT_IDPMGMT_URL'],self.cat_inst_id)
            except:
                return False
        return False

    cat_active.boolean = True
    cat_active.short_description = "CAT profiles"
