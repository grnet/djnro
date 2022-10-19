# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from collections import namedtuple
from functools import partial
import uuid
from django.utils.inspect import getargspec
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields
from django.utils.functional import curry
from django.utils.text import capfirst
from django.utils import six
from django.core import exceptions
from django.conf import settings
from django import forms
from django.core.exceptions import ValidationError
from django.utils.encoding import (
    force_text, python_2_unicode_compatible
)
from sortedm2m.fields import SortedManyToManyField
from utils.functional import cached_property


_VENUE_INFO_HELP_TEXT = _(
    'IEEE 802.11-2012, clause 8.4.1.34 Venue Info. This is a pair of integers, '
    'each between 0 and 255, separated with ",".'
)

def validate_venue_info(value):
    subfields = value.split(',')
    if len(subfields) != 2:
        return False
    for subfield in subfields:
        if not 0 <= int(subfield) <= 255:
            return False
    return True


def get_choices_from_settings(setting):
    return getattr(settings, setting, tuple())


class MultiSelectFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        supercls = super(MultiSelectFormField, self)
        # remove TypedChoiceField extra args
        supercls_init_args = getargspec(supercls.__init__)[0]
        if supercls_init_args[0:0] == ['self']:
            del supercls_init_args[0]
        supercls.__init__(
            *args,
            **{key: val for (key, val) in kwargs.items()
               if key in supercls_init_args}
        )

class MultiSelectField(models.Field):
    _separator_default = ','

    def __init__(self, *args, **kwargs):
        self.separator = kwargs.pop(
            'separator', self._separator_default)
        super(MultiSelectField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(
            MultiSelectField, self).deconstruct()
        if self.separator != self._separator_default:
            kwargs['separator'] = self.separator
        return name, path, args, kwargs

    def get_internal_type(self):
        return "CharField"

    def get_choices(self, *args, **kwargs):
        if self.blank:
            kwargs['include_blank'] = False
        return super(MultiSelectField, self).get_choices(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'choices_form_class': MultiSelectFormField
        }
        defaults.update(kwargs)
        return super(MultiSelectField, self).formfield(**defaults)

    def get_prep_value(self, value):
        if isinstance(value, six.string_types):
            value = value.split(self.separator) if value else []
        if isinstance(value, (list, set)):
            return self.separator.join(sorted(set(value)))
        return ''

    def from_db_value(self, value, *_):
        return sorted(set(value.split(self.separator))) \
            if value not in ('', None) else []

    def to_python(self, value):
        if isinstance(value, six.string_types):
            value = value.split(self.separator) if value else []
        if isinstance(value, (list, set)):
            return sorted(set(value))
        return []

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(MultiSelectField, self).contribute_to_class(
            cls, name, *args, **kwargs)
        if self.choices:
            def _get_FIELD_display(self, field):
                values = getattr(self, field.attname)
                choices = dict(field.flatchoices)
                return field.separator.join([
                    force_text(
                        choices.get(value, value),
                        strings_only=True
                    )
                    for value in values
                ])
            setattr(cls, 'get_%s_display' % self.name,
                    curry(_get_FIELD_display, field=self))

    def validate(self, value, model_instance):
        # assume value should be a list
        if not isinstance(value, list):
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )
        if not value and not self.null:
            raise ValidationError(
                self.error_messages['null'],
                code='null'
            )
        for option in value:
            super(MultiSelectField, self).validate(
                option, model_instance
            )
        return

@MultiSelectField.register_lookup
class DelimitedValueExactLookup(models.lookups.PatternLookup):
    lookup_name = 'exact'

    delimited_patterns = (
        ('contains', '%%{delimiter}%s{delimiter}%%'),
        ('startswith', '%s{delimiter}%%'),
        ('endswith', '%%{delimiter}%s'),
    )

    def as_sql(self, compiler, connection):
        lhs, lhs_params = compiler.compile(self.lhs)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        sql = '%s %s' % (lhs, self.get_rhs_op(connection, rhs))

        try:
            delimiter = self.lhs.field.separator
        except AttributeError:
            delimiter = ''
        for lookup_name, pattern_replacement in self.delimited_patterns:
            self.lookup_name = lookup_name
            pattern = pattern_replacement.format(delimiter=delimiter)
            rhs, rhs_params = self.process_rhs_pattern(
                compiler, connection, pattern
            )
            sql += ' OR %s %s' % (
                lhs,
                self.get_rhs_op(connection, rhs)
            )
            params += lhs_params + rhs_params
        self.lookup_name = DelimitedValueExactLookup.lookup_name
        return sql, params

    def process_rhs_pattern(self, qn, connection, pattern):
        rhs, params = super(DelimitedValueExactLookup, self).process_rhs(
            qn, connection)
        if params and not self.bilateral_transforms:
            params[0] = pattern % connection.ops.prep_for_like_query(params[0])
        return rhs, params

class CharField(models.CharField):
    pass

@CharField.register_lookup
class MysqlCollateBinExactLookup(models.lookups.Exact):
    lookup_name = 'bexact'

    def get_mysql_collation(self, conn):
        try:
            collation = self.lhs._mysql_collation # pylint: disable=protected-access
        except AttributeError:
            statement = "SHOW FULL COLUMNS FROM {} WHERE field = %s".format(
                self.lhs.alias)
            field = self.lhs.field
            column = field.db_column or field.name
            with conn.cursor() as cursor:
                cursor.execute(statement, (column,))
                nt_result = namedtuple(
                    'res', [c[0] for c in cursor.description])
                row = cursor.fetchone()
            collation = nt_result(*row).Collation
            self.lhs._mysql_collation = collation # pylint: disable=protected-access
        charset, _collation = collation.split('_', 1)
        if _collation.endswith('_ci'):
            _collation = 'bin'
        new_collation = '_'.join((charset, _collation))
        return collation, new_collation

    def as_mysql(self, compiler, connection):
        orig_collation, new_collation = self.get_mysql_collation(connection)
        if orig_collation == new_collation:
            sup = super(MysqlCollateBinExactLookup, self)
            parent = getattr(sup, 'as_mysql', sup.as_sql)
            self.lookup_name = 'exact'
            return parent(compiler, connection)
        self.lookup_name = 'exact'
        lhs, lhs_params = compiler.compile(self.lhs)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        sql = '%s %s COLLATE %s' % (lhs, self.get_rhs_op(connection, rhs),
                                    new_collation)
        self.lookup_name = MysqlCollateBinExactLookup.lookup_name
        return sql, params

# https://www.djangosnippets.org/snippets/2402/
def get_namedtuple_choices(*choices_tuples):
    """
    Return an object resembling PY3 enum, by means of collections.namedtuple

    :param choices_tuples: Sequence of tuples, each containing at least 3
        members: symbolic name (for attribute lookup), value, description (the
        latter 2 as required for Django choices); additional members are
        ignored

    :return: Choices(tuple) instance
    """
    names = [tup[0] for tup in choices_tuples]
    vals = [tup[1:3] for tup in choices_tuples]
    class Choices(namedtuple('Choices', names)):
        def __getattribute__(self, name):
            """
            If the value is a tuple, return the first member; attribute lookup
            on a choices object thus returns only the value, rather than
            (value, description)
            """
            attr = super(Choices, self).__getattribute__(name)
            if not isinstance(attr, tuple):
                return attr
            return attr[0]
        def __contains__(self, item):
            """
            If the argument is not a tuple, membership test checks against the
            first member rather than the whole tuple (value, description)
            """
            if not isinstance(item, tuple):
                return item in (val[0] for val in self.__iter__())
            return super(Choices, self).__contains__(item)
    return Choices._make(vals)

# Last member in choices tuples maps numeric to string (EDB2) ERTYPE
_ERTYPES = (
    ('IDP', 1, 'IdP only', 'IdP'),
    ('SP', 2, 'SP only', 'SP'),
    ('IDPSP', 3, 'IdP and SP', 'IdP+SP'),
)
ERTYPES = get_namedtuple_choices(*_ERTYPES)
ERTYPE_ROLES = get_namedtuple_choices(*(
    (cat.upper(), [val for val, descr in ERTYPES if cat in descr])
    for cat in ('IdP', 'SP')
))
def get_ertype_string(ertype, reverse=False):
    """
    Map an ERTYPE number to the respective string, or vice versa if reverse
    """
    return dict(map(lambda x: (x[-1], x[1]) if reverse else (x[1], x[-1]),
                    _ERTYPES))[ertype]
get_ertype_number = partial(get_ertype_string, reverse=True) # pylint: disable=invalid-name

RADPROTOS = get_namedtuple_choices(
    ('UDP', 'radius', 'traditional RADIUS over UDP'),
    # ('TCP', 'radius-tcp', 'RADIUS over TCP (RFC6613)'),
    # ('TLS', 'radius-tls', 'RADIUS over TLS (RFC6614)'),
    # ('DTLS', 'radius-dtls', 'RADIUS over datagram TLS (RESERVED)'),
)


ADDRTYPES = get_namedtuple_choices(
    ('ANY', 'any', 'Default'),
    ('IPV4', 'ipv4', 'IPv4 only'),
    #('IPV6', 'ipv6', 'IPv6 only'), # Commented for the time...not yet in use
)

RADTYPES = get_namedtuple_choices(
    ('AUTH', 'auth', 'Handles Access-Request packets only'),
    ('ACCT', 'acct', 'Handles Accounting-Request packets only'),
    ('AUTHACCT', 'auth+acct', 'Handles both Access-Request and Accounting-Request packets'),
)

PRODUCTION_STATES = get_namedtuple_choices(
    ('TEST', 0, 'preproduction/test'),
    ('ACTIVE', 1, 'active'),
)

CONTACT_TYPES = get_namedtuple_choices(
    ('PERSON', 0, 'person'),
    ('SERVCE', 1, 'service/department'),
)

CONTACT_PRIVACY = get_namedtuple_choices(
    ('PRIVATE', 0, 'private'),
    ('PUBLIC', 1, 'public'),
)
EDB_SERVER_TYPES = get_namedtuple_choices(
    ('UDP', 0, 'UDP'),
    ('TLS', 1, 'TLS'),
    ('FTICKS', 2, 'F-ticks'),
)


@python_2_unicode_compatible
class Name_i18n(models.Model):
    '''
    Name in a particular language
    '''

    name = CharField(max_length=255)
    lang = models.CharField(max_length=5, choices=get_choices_from_settings('URL_NAME_LANGS'))
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Name (i18n)"
        verbose_name_plural = "Names (i18n)"

    @staticmethod
    def get_name_factory(reverse_accessor):
        def get_name(self, lang=None):
            manager = getattr(self, reverse_accessor)
            def all_names(**kwargs):
                names_qs = manager.filter(**kwargs) \
                    if kwargs else \
                    manager.all()
                return ', '.join([n.name for n in names_qs])
            if not lang:
                return all_names()
            try:
                return manager.get(lang=lang).name
            except Name_i18n.DoesNotExist:
                return all_names()
            except Name_i18n.MultipleObjectsReturned:
                return all_names(lang=lang)
        return get_name


@python_2_unicode_compatible
class Contact(models.Model):
    '''
    Contact
    '''

    name = CharField(max_length=255, db_column='contact_name')
    email = models.CharField(max_length=80, db_column='contact_email')
    phone = models.CharField(max_length=80, db_column='contact_phone')
    type = models.PositiveIntegerField(
        choices=CONTACT_TYPES,
        default=CONTACT_TYPES.PERSON,
        db_column='contact_type'
    )
    privacy = models.PositiveIntegerField(
        choices=CONTACT_PRIVACY,
        default=CONTACT_PRIVACY.PRIVATE,
        db_column='contact_privacy'
    )

    def __str__(self):
        return '%s <%s> (%s)' % (self.name, self.email, self.phone)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"


@python_2_unicode_compatible
class Coordinates(models.Model):
    longitude = models.DecimalField(
        max_digits=12, decimal_places=8, help_text=_(
            'Longitude in decimal degrees, up to 8 decimal places'
        ))
    latitude = models.DecimalField(
        max_digits=12, decimal_places=8, help_text=_(
            'Latitude in decimal degrees, up to 8 decimal places'
        ))
    altitude = models.DecimalField(
        max_digits=7, decimal_places=3, null=True, help_text=_(
            'Altitude, up to 9999 meters with millimeter precision'
        ))

    def __str__(self):
        coordinates_str = 'Lat {}, Lon {}'.format(self.latitude, self.longitude)
        if self.altitude is not None:
            coordinates_str += ', Alt {}'.format(self.altitude)
        return coordinates_str

    class Meta:
        verbose_name = "Coordinates"
        verbose_name_plural = "Coordinates"


@python_2_unicode_compatible
class InstitutionContactPool(models.Model):
    contact = models.OneToOneField(Contact)
    institution = models.ForeignKey("Institution")

    def __str__(self):
        return u"%s:%s" %(self.contact, self.institution)

    class Meta:
        verbose_name = "Instutution Contact (Pool)"
        verbose_name_plural = "Instutution Contacts (Pool)"


@python_2_unicode_compatible
class URL_i18n(models.Model):
    '''
    URL of a particular type in a particular language
    '''

    URLTYPES = (
        ('info', 'Info'),
        ('policy', 'Policy'),
    )
    url = models.CharField(max_length=180, db_column='URL')
    lang = models.CharField(max_length=5, choices=get_choices_from_settings('URL_NAME_LANGS'))
    urltype = models.CharField(max_length=10, choices=URLTYPES, db_column='type')
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Url (i18n)"
        verbose_name_plural = "Urls (i18n)"

    def __str__(self):
        return self.url


@python_2_unicode_compatible
class Address_i18n(models.Model):
    '''
    Address in a particular language
    '''

    street = CharField(max_length=255)
    city = CharField(max_length=255)
    lang = models.CharField(max_length=5, choices=get_choices_from_settings('URL_NAME_LANGS'))
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = fields.GenericForeignKey('content_type', 'object_id')

    _str_include_lang = True

    def __str__(self):
        addr_str = ', '.join([f for f in (self.street, self.city) if f])
        if self._str_include_lang:
            addr_str = six.text_type('{}: {}').format(
                self.lang.upper(), addr_str)
        return addr_str

    class Meta:
        verbose_name = "Address (i18n)"
        verbose_name_plural = "Addresses (i18n)"

    @staticmethod
    def get_address_factory(reverse_accessor):
        def get_address(self, lang=None, default_lang_fallback=True):
            lang_default = getattr(settings, 'LANGUAGE_CODE', 'en')
            manager = getattr(self, reverse_accessor)
            if lang is None:
                lang = lang_default
            addr = manager.filter(lang=lang).first()
            if addr is None and default_lang_fallback and lang != lang_default:
                addr = manager.filter(lang=lang_default).first()
            if isinstance(addr, Address_i18n):
                addr._str_include_lang = False
            return addr
        return get_address


@python_2_unicode_compatible
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

    def __str__(self):
        return '%s' % self.realm

    def get_servers(self):
        return ",".join(["%s" % x for x in self.proxyto.all()])


@python_2_unicode_compatible
class InstServer(models.Model):
    '''
    Server of an Institution
    '''
    # instid = models.ForeignKey("Institution", null=True)
    # instid_m2m = models.ManyToManyField('Institution', related_name='servers_tmp', default = 'none')
    instid = models.ManyToManyField('Institution', related_name='servers', blank=True)
    ertype = models.PositiveIntegerField(choices=ERTYPES, db_column='type')
    # ertype:
    # 1: accept if instid.ertype: 1 (idp) or 3 (idpsp)
    # 2: accept if instid.ertype: 2 (sp) or 3 (idpsp)
    # 3: accept if instid.ertype: 3 (idpsp)

    # hostname/ipaddr or descriptive label of server
    name = models.CharField(max_length=80, help_text=_("Descriptive label"), null=True, blank=True) # ** (acts like a label)
    # hostname/ipaddr of server, overrides name
    addr_type = models.CharField(max_length=16, choices=ADDRTYPES, default=ADDRTYPES.IPV4)
    host = models.CharField(max_length=80, help_text=_("IP address | FQDN hostname")) # Handling with FQDN parser or ipaddr (google lib) * !!! Add help text to render it in template (mandatory, unique)
    #TODO: Add description field or label field
    # accept if type: 1 (idp) or 3 (idpsp) (for the folowing 4 fields)
    rad_pkt_type = models.CharField(max_length=48, choices=RADTYPES, default=RADTYPES.AUTHACCT, null=True, blank=True,)
    auth_port = models.PositiveIntegerField(null=True, blank=True, default=1812, help_text=_("Default for RADIUS: 1812")) # TODO: Also ignore while exporting XML
    acct_port = models.PositiveIntegerField(null=True, blank=True, default=1813, help_text=_("Default for RADIUS: 1813"))
    status_server = models.BooleanField(help_text=_("Do you accept Status-Server requests?"))

    secret = models.CharField(max_length=80)
    proto = models.CharField(max_length=12, choices=RADPROTOS, default=RADPROTOS.UDP)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Institution Server"
        verbose_name_plural = "Institutions' Servers"

    def __str__(self):
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

    def clean(self):
        if not self.pk:
            return
        if self.ertype == ERTYPES.SP:
            realms = self.instrealm_set.all()
            # If a server is a proxy for a realm, can not change type to SP
            if realms.count() > 0:
                raise ValidationError(
                    {'ertype': _(
                            'You cannot change this server to %(ertype)s (it is'
                            ' used by realms %(realms)s)') % {
                            'ertype': self.get_ertype_display(),
                            'realms': ', '.join([r.realm for r in realms])
                            }
                     }
                    )


@python_2_unicode_compatible
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

    def __str__(self):
        return "%s-%s" % (self.realm.realm, self.mon_type)
#    def __str__(self):
#        return _('Institution: %(inst)s, Monitored Realm: %(monrealm)s, Monitoring Type: %(montype)s') % {
#        # but name is many-to-many from institution
#            'inst': self.instid.name,
#            'monrealm': self.realm,
#            'montype': self.mon_type,
#            }


@python_2_unicode_compatible
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

    def __str__(self):
        return _('Monitored Realm: %(monrealm)s, Proxyback Client: %(servername)s') % {
            # but name is many-to-many from institution
            'monrealm': self.instrealmmonid.realm,
            'servername': self.name,
        }


@python_2_unicode_compatible
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

    def __str__(self):
        return _('Monitored Realm: %(monrealm)s, EAP Method: %(eapmethod)s, Phase 2: %(phase2)s, Username: %(username)s') % {
            # but name is many-to-many from institution
            'monrealm': self.instrealmmonid.realm,
            'eapmethod': self.eap_method,
            'phase2': self.phase2,
            'username': self.username,
        }


@python_2_unicode_compatible
class ServiceLoc(models.Model):
    '''
    Service Location of an SP/IdPSP Institution
    '''

    GEO_TYPES = get_namedtuple_choices(
        ('SPOT', 0, 'single spot'),
        ('AREA', 1, 'area'),
        ('MOBILE', 2, 'mobile'),
    )

    PHYSICAL_AVAILABILITY_STATES = get_namedtuple_choices(
        ('ALWAYS', 0, 'no restrictions'),
        ('RESTRICTED', 1, 'physical access restrictions'),
    )

    ENCTYPES = (
        ('WPA/TKIP', 'WPA-TKIP'),
        ('WPA/AES', 'WPA-AES'),
        ('WPA2/TKIP', 'WPA2-TKIP'),
        ('WPA2/AES', 'WPA2-AES'),
        ('WPA3/AES', 'WPA3-AES'),
    )

    LOCATION_TAGS = (
        ('port_restrict', 'port restrictions'),
        ('transp_proxy', 'transparent proxy'),
        ('IPv6', 'IPv6'),
        ('NAT', 'NAT'),
        ('HS2.0', 'Passpoint (Hotspot 2.0)'),
    )

    # accept if institutionid.ertype: 2 (sp) or 3 (idpsp)
    institutionid = models.ForeignKey("Institution", verbose_name="Institution")
    locationid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # single set of coordinates enforced by .signals.sloc_coordinates_enforce_one
    coordinates = SortedManyToManyField(Coordinates)
    stage = models.PositiveIntegerField(
        choices=PRODUCTION_STATES,
        default=PRODUCTION_STATES.ACTIVE
    )
    geo_type = models.PositiveIntegerField(
        choices=GEO_TYPES,
        default=GEO_TYPES.SPOT,
        db_column='type'
    )
    # TODO: multiple names can be specified [...] name in English is required
    loc_name = fields.GenericRelation(Name_i18n)
    # TODO: multiple addresses can be specified [...] address in English is required
    address = fields.GenericRelation(Address_i18n)
    venue_info = models.CharField(
        max_length=7,
        blank=True,
        validators=[validate_venue_info],
        db_column='location_type',
        help_text=_VENUE_INFO_HELP_TEXT
    )
    contact = models.ManyToManyField(Contact, blank=True)
    SSID = models.CharField(max_length=16)
    enc_level = MultiSelectField(max_length=64, choices=ENCTYPES, blank=True, null=True)
    tag = MultiSelectField(max_length=64, choices=LOCATION_TAGS, blank=True)
    AP_no = models.PositiveIntegerField(blank=True, null=True)
    wired_no = models.PositiveIntegerField(blank=True, null=True)
    physical_avail = models.PositiveIntegerField(
        choices=PHYSICAL_AVAILABILITY_STATES,
        default=PHYSICAL_AVAILABILITY_STATES.ALWAYS,
        db_column='availability',
        help_text=_('Restrictions regarding physical access to the service '
                    'area')
    )
    operation_hours = models.CharField(max_length=255, blank=True, help_text=_(
        'Free text description of opening hours, if service is not available '
        '24 hours per day'
    ))
    # only urltype = 'info' should be accepted here
    url = fields.GenericRelation(URL_i18n, blank=True, null=True)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Service Location"
        verbose_name_plural = "Service Locations"

    def __str__(self):
        return _('Institution: %(inst)s, Service Location: %(locname)s') % {
            # but name is many-to-many from institution
            'inst': self.institutionid,
            # but locname is many-to-many
            'locname': self.get_name(),
        }

    get_name = Name_i18n.get_name_factory('loc_name')
    get_name.short_description = 'Location Name'

    get_address = Address_i18n.get_address_factory('address')
    get_address.short_description = 'Location Address'

    @cached_property
    def latitude(self):
        try:
            return self.coordinates.first().latitude
        except AttributeError:
            return None
    @latitude.setter
    def latitude(self, value):
        return value
    @latitude.deleter
    def latitude(self, value):
        try:
            self.coordinates.filter(latitude=value).first().delete()
        except AttributeError:
            pass

    @cached_property
    def longitude(self):
        try:
            return self.coordinates.first().longitude
        except AttributeError:
            return None
    @longitude.setter
    def longitude(self, value):
        return value
    @longitude.deleter
    def longitude(self, value):
        try:
            self.coordinates.filter(longitude=value).first().delete()
        except AttributeError:
            pass


@python_2_unicode_compatible
class Institution(models.Model):
    '''
    Institution
    '''

    realmid = models.ForeignKey("Realm")
    instid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    org_name = fields.GenericRelation(Name_i18n)
    inst_name = fields.GenericRelation(Name_i18n)
    ertype = models.PositiveIntegerField(choices=ERTYPES, db_column='type')
    stage = models.PositiveIntegerField(
        choices=PRODUCTION_STATES,
        default=PRODUCTION_STATES.ACTIVE
    )

    def __str__(self):
        return "%s" % ', '.join([i.name for i in self.org_name.all()])

    get_name = Name_i18n.get_name_factory('org_name')

    def get_active_cat_enrl(self, cat_instance='production'):
        urls = []
        active_cat_enrl = self.catenrollment_set.filter(url='ACTIVE', cat_instance=cat_instance)
        for catenrl in active_cat_enrl:
            if catenrl.cat_configuration_url:
                urls.append(catenrl.cat_configuration_url)
        return urls

    def get_active_cat_ids(self, cat_instance='production'):
        ids = []
        active_cat_enrl = self.catenrollment_set.filter(url='ACTIVE', cat_instance=cat_instance)
        for catenrl in active_cat_enrl:
            ids.append(catenrl.cat_inst_id)
        return ids


@python_2_unicode_compatible
class InstitutionDetails(models.Model):
    '''
    Institution Details
    '''
    institution = models.OneToOneField(Institution)
    # TODO: multiple addresses can be specified [...] address in English is required
    address = fields.GenericRelation(Address_i18n)
    coordinates = models.ForeignKey(
        Coordinates,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    contact = models.ManyToManyField(Contact)
    url = fields.GenericRelation(URL_i18n)
    # accept if ertype: 2 (sp) or 3 (idpsp) (Applies to the following field)
    oper_name = models.CharField(
        max_length=252,
        null=True,
        blank=True,
        help_text=_('The primary, registered domain name for your institution, eg. example.com.<br>This is used to derive the Operator-Name attribute according to RFC5580, par.4.1, using the REALM namespace.')
    )
    venue_info = models.CharField(
        max_length=7,
        blank=True,
        validators=[validate_venue_info],
        db_column='inst_type',
        help_text=_VENUE_INFO_HELP_TEXT
    )
    # accept if ertype: 1 (idp) or 3 (idpsp) (Applies to the following field)
    number_user = models.PositiveIntegerField(null=True, blank=True, help_text=_("Number of users (individuals) that are eligible to participate in eduroam service"))
    number_id = models.PositiveIntegerField(null=True, blank=True, help_text=_("Number of issued e-identities (credentials) that may be used for authentication in eduroam service"))
    ts = models.DateTimeField(auto_now=True)

    get_address = Address_i18n.get_address_factory('address')
    get_address.short_description = 'Institution Address'

    class Meta:
        verbose_name = "Institutions' Details"
        verbose_name_plural = "Institution Details"

    def __str__(self):
        return _('Institution: %(inst)s, Type: %(ertype)s') % {
            # but name is many-to-many from institution
            'inst': ', '.join([i.name for i in self.institution.org_name.all()]),
            'ertype': self.institution.get_ertype_display(),
        }

    def get_inst_name(self):
        return ", ".join([i.name for i in self.institution.org_name.all()])
    get_inst_name.short_description = "Institution Name"


@python_2_unicode_compatible
class Realm(models.Model):
    '''
    Realm
    '''

    roid = models.CharField(
        max_length=255,
        default=getattr(settings, 'NRO_ROID'),
        unique=True,
        db_column='ROid'
    )
    country = models.CharField(max_length=5, choices=get_choices_from_settings('REALM_COUNTRIES'))
    stype = 0 # hard-coded (FLRS)
    stage = models.PositiveIntegerField(
        choices=PRODUCTION_STATES,
        default=PRODUCTION_STATES.ACTIVE
    )
    # TODO: multiple names can be specified [...] name in English is required
    org_name = fields.GenericRelation(Name_i18n)
    # TODO: multiple addresses can be specified [...] address in English is required
    address = fields.GenericRelation(Address_i18n)
    coordinates = models.ForeignKey(
        Coordinates,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    contact = models.ManyToManyField(Contact)
    url = fields.GenericRelation(URL_i18n)
    ts = models.DateTimeField(auto_now=True)

    get_address = Address_i18n.get_address_factory('address')
    get_address.short_description = 'Realm Address'

    class Meta:
        verbose_name = "Realm"
        verbose_name_plural = "Realms"

    def __str__(self):
        return _('Country: %(country)s, NRO: %(orgname)s') % {
            # but name is many-to-many from institution
            'orgname': ', '.join([i.name for i in self.org_name.all()]),
            'country': self.country,
        }

    get_name = Name_i18n.get_name_factory('org_name')


# TODO: this represents a *database view* "realm_data", find a better way to write it
@python_2_unicode_compatible
class RealmData(models.Model):
    '''
    Realm statistics
    '''

    realmid = models.OneToOneField(Realm)
    # db: select count(institution.id) as number_inst from institution, realm where institution.realmid == realm.realmid
    number_inst = models.PositiveIntegerField(editable=False)
    # db: select sum(institution.number_user) as number_user from institution, realm where institution.realmid == realm.realmid
    number_user = models.PositiveIntegerField(editable=False)
    # db: select sum(institution.number_id) as number_id from institution, realm where institution.realmid == realm.realmid
    number_id = models.PositiveIntegerField(editable=False)
    # db: select count(institution.id) as number_IdP from institution, realm where institution.realmid == realm.realmid and institution.type == 1
    number_IdP = models.PositiveIntegerField(editable=False)
    # db: select count(institution.id) as number_SP from institution, realm where institution.realmid == realm.realmid and institution.type == 2
    number_SP = models.PositiveIntegerField(editable=False)
    # db: select count(institution.id) as number_IdPSP from institution, realm where institution.realmid == realm.realmid and institution.type == 3
    number_IdPSP = models.PositiveIntegerField(editable=False)
    # db: select greatest(max(realm.ts), max(institution.ts)) as ts from institution, realm where institution.realmid == realm.realmid
    ts = models.DateTimeField(editable=False)

    def __str__(self):
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


@python_2_unicode_compatible
class RealmServer(models.Model):
    '''NRO realm servers'''

    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='servers')
    server_name = models.CharField(max_length=80, help_text=_("IP address | FQDN hostname"))
    server_type = models.PositiveIntegerField(
        choices=EDB_SERVER_TYPES,
        help_text=_("Realm server type")
    )

    class Meta:
        verbose_name = "Realm Server"
        verbose_name_plural = "Realms' Servers"

    def __str__(self):
        return _('ROid: %(roid)s, Server: %(servername)s, Type: %(type)s') % {
            'roid': self.realm.roid,
            'servername': self.server_name,
            'type': next((t[1] for t in EDB_SERVER_TYPES if t[0] == self.server_type), self.server_type),
        }


@python_2_unicode_compatible
class CatEnrollment(models.Model):
    ''' eduroam CAT enrollment '''

    ACTIVE = u"ACTIVE"

    cat_inst_id = models.PositiveIntegerField()
    inst = models.ForeignKey(Institution)
    url = models.CharField(max_length=255, blank=True, null=True, help_text="Set to ACTIVE if institution has CAT profiles")
    cat_instance = models.CharField(max_length=50, choices=get_choices_from_settings('CAT_INSTANCES'))
    applier = models.ForeignKey(settings.AUTH_USER_MODEL)
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['inst', 'cat_instance']

    def __str__(self):
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
