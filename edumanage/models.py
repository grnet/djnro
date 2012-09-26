# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

'''
TODO main description
'''

from django.db import models
from django.utils.translation import ugettext as _

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


LANGS = (
        ('en', 'English' ),
        ('el', 'Ελληνικά'),
    )


# FIXME: use idp, sp, idpsp as keys not in the velue part. Get rid of 1,2,3
ERTYPES = (
        (1, 'idp: IdP only' ),
        (2, 'sp: SP only'),
        (3, 'idpsp: IdP and SP'),
    )

RADPROTOS = (
        ('radius', 'traditional RADIUS over UDP' ),
        ('radius-tcp', 'RADIUS over TCP (RFC6613)'),
        ('radius-tls', 'RADIUS over TLS (RFC6614)'),
        ('radius-dtls', 'RADIUS over datagram TLS (RESERVED)'),
    )


class Name_i18n(models.Model):
    '''
    Name in a particular language
    '''

    name = models.CharField(max_length=80)
    lang = models.CharField(max_length=5, choices=LANGS)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name
        

class Contact(models.Model):
    '''
    Contact
    '''

    firstname = models.CharField(max_length=80, db_column='contact_firstname')
    lastname = models.CharField(max_length=80, db_column='contact_lastname')
    email = models.CharField(max_length=80, db_column='contact_email')
    phone = models.CharField(max_length=80, db_column='contact_phone')

    def __unicode__(self):
        return '%s %s <%s> (%s)' % (self.firstname, self.lastname, self.email, self.phone)

class URL_i18n(models.Model):
    '''
    URL of a particular type in a particular language
    '''

    URLTYPES = (
                ('info', 'Info' ),
                ('policy', 'Policy'),
               )
    url = models.CharField(max_length=180, db_column='URL')
    lang = models.CharField(max_length=5, choices=LANGS)
    urltype = models.CharField(max_length=10, choices=URLTYPES, db_column='type')

    def __unicode__(self):
        return self.url

class InstRealm(models.Model):
    '''
    Realm (including wildcards) of an IdP Institution
    '''

    realmexpr = models.CharField(max_length=20)
    priority = models.PositiveIntegerField(max_length=3)
    instid = models.ForeignKey("Institution")
    # accept if instid.ertype: 1 (idp) or 3 (idpsp)
    proxyto = models.ManyToManyField("InstServer")

    def __unicode__(self):
        return _('Institution: %(inst)s, Realm: %(realmexpr)s, Priority: %(priority)s') % {
        # but name is many-to-many from institution
            'inst': self.instid.name,
            'realmexpr': self.realmexpr,
            'priority': self.priority,
            }

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
    name = models.CharField(max_length=80)
    # hostname/ipaddr of server, overrides name
    host = models.CharField(max_length=80)

    # accept if type: 1 (idp) or 3 (idpsp)
    port = models.PositiveIntegerField(max_length=5)
    acct_port = models.PositiveIntegerField(max_length=5)
    timeout = models.PositiveIntegerField(max_length=2)
    retry = models.PositiveIntegerField(max_length=2)

    status_server = models.BooleanField()
    secret = models.CharField(max_length=16)
    proto = models.CharField(max_length=12, choices=RADPROTOS)
    ts = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return _('Institution: %(inst)s, Server: %(servername)s, Type: %(ertype)s') % {
        # but name is many-to-many from institution
            'inst': self.instid.name,
            'servername': self.name,
        # the human-readable name would be nice here
            'ertype': self.ertype,
            }    
    
    
class InstRealmMon(models.Model):
    '''
    Realm of an IdP Institution to be monitored
    '''

    MONTYPES = (
                ('local', 'Institution provides account for the NRO to monitor the realm' ),
                ('proxyback', 'Institution proxies the realm back to the NRO'),
               )

    instid = models.ForeignKey("Institution")
    realm = models.CharField(max_length=20)
    mon_type = models.CharField(max_length=8, choices=MONTYPES)

    def __unicode__(self):
        return _('Institution: %(inst)s, Monitored Realm: %(monrealm)s, Monitoring Type: %(montype)s') % {
        # but name is many-to-many from institution
            'inst': self.instid.name,
            'monrealm': self.realm,
            'montype': self.mon_type,
            }

class MonProxybackClient(models.Model):
    '''
    Server of an Institution that will be proxying back requests for a monitored realm
    '''

    instrealmmonid = models.ForeignKey("InstRealmMon")
    # hostname/ipaddr or descriptive label of server
    name = models.CharField(max_length=80)
    # hostname/ipaddr of server, overrides name
    host = models.CharField(max_length=80)
    status_server = models.BooleanField()
    secret = models.CharField(max_length=16)
    proto = models.CharField(max_length=12, choices=RADPROTOS)
    ts = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return _('Institution: %(inst)s, Monitored Realm: %(monrealm)s, Proxyback Client: %(servername)s') % {
        # but name is many-to-many from institution
            'inst': self.instid.name,
            'monrealm': self.instrealmmonid.realm,
            'servername': self.name,
            }

class MonLocalEAPOLData(models.Model):
    '''
    EAPOL data for an old-style monitored realm
    '''

    EAPTYPES = (
                ('PEAP', 'EAP-PEAP' ),
                ('TTLS', 'EAP-TTLS'),
                ('TLS', 'EAP-TLS'),
               )
    EAP2TYPES = (
                ('PAP', 'PAP' ),
                ('CHAP', 'CHAP'),
                ('MS-CHAPv2', 'MS-CHAPv2'),
               )
    MONRESPTYPES = (
                ('accept', 'Access-Accept expected' ),
                ('reject', 'Access-Reject expected'),
                ('both', 'RESERVED'),
               )

    instrealmmonid = models.ForeignKey("InstRealmMon")
    eap_method = models.CharField(max_length=16, choices=EAPTYPES)
    phase2 = models.CharField(max_length=16, choices=EAP2TYPES)
    # only local-part, no realm
    username = models.CharField(max_length=24)
    passwp = models.CharField(max_length=24, db_column='pass')
    cert = models.CharField(max_length=32)
    exp_response = models.CharField(max_length=6, choices=MONRESPTYPES)

    def __unicode__(self):
        return _('Institution: %(inst)s, Monitored Realm: %(monrealm)s, EAP Method: %(eapmethod)s, Phase 2: %(phase2)s, Username: %(username)s') % {
        # but name is many-to-many from institution
            'inst': self.instid.name,
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
                ('WPA/TKIP', 'WPA-TKIP' ),
                ('WPA/AES', 'WPA-AES'),
                ('WPA2/TKIP', 'WPA2-TKIP'),
                ('WPA2/AES', 'WPA2-AES'),
               )

    # accept if institutionid.ertype: 2 (sp) or 3 (idpsp)
    institutionid = models.ForeignKey("Institution")
    longitude = models.DecimalField(max_digits=8, decimal_places=6)
    latitude = models.DecimalField(max_digits=8, decimal_places=6)
    # TODO: multiple names can be specified [...] name in English is required
    loc_name = generic.GenericRelation(Name_i18n)
    address_street = models.CharField(max_length=32)
    address_city = models.CharField(max_length=24)
    contact = models.ManyToManyField(Contact)
    SSID = models.CharField(max_length=16)
    enc_level = models.CharField(max_length=10, choices=ENCTYPES)
    port_restrict = models.BooleanField()
    transp_proxy = models.BooleanField()
    IPv6 = models.BooleanField()
    NAT = models.BooleanField()
    AP_no = models.PositiveIntegerField(max_length=3)
    wired = models.BooleanField()
    # only urltype = 'info' should be accepted here
    url = models.ManyToManyField(URL_i18n)
    ts = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return _('Institution: %(inst)s, Service Location: %(locname)s') % {
        # but name is many-to-many from institution
            'inst': self.institutionid,
        # but locname is many-to-many
            'locname': self.loc_name,
            }
    
    
    def get_name(self, lang=None):
        name = ', '.join([i.name for i in self.loc_name.all()])
        if not lang:
            return name
        else:
            try:
                name = self.loc_name.get(lang=lang)
                return name
            except Exception as e:
                return name

class Institution(models.Model):
    '''
    Institution
    '''
    
    realmid = models.ForeignKey("Realm")
    org_name = generic.GenericRelation(Name_i18n)
    
    
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
            except Exception as e:
                return name
            

class InstitutionDetails(models.Model):
    '''
    Institution Details
    '''
    institution = models.OneToOneField(Institution)
    ertype = models.PositiveIntegerField(max_length=1, choices=ERTYPES, db_column='type')
    # TODO: multiple names can be specified [...] name in English is required
    address_street = models.CharField(max_length=32)
    address_city = models.CharField(max_length=24)
    contact = models.ManyToManyField(Contact)
    url = models.ManyToManyField(URL_i18n)
    # accept if ertype: 2 (sp) or 3 (idpsp)
    oper_name = models.CharField(max_length=24)
    # accept if ertype: 1 (idp) or 3 (idpsp)
    number_user = models.PositiveIntegerField(max_length=6)
    number_id = models.PositiveIntegerField(max_length=6)
    ts = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return _('Institution: %(inst)s, Type: %(ertype)s') % {
        # but name is many-to-many from institution
            'inst': ', '.join([i.name for i in self.institution.org_name.all()]),
            'ertype': self.ertype,
            }



class Realm(models.Model):
    '''
    Realm
    '''

    COUNTRIES = (
                ('gr', 'Greece' ),
               )

    country = models.CharField(max_length=2, choices=COUNTRIES)
    stype = models.PositiveIntegerField(max_length=1, default=0, editable=False)
    # TODO: multiple names can be specified [...] name in English is required
    org_name = generic.GenericRelation(Name_i18n)
    address_street = models.CharField(max_length=32)
    address_city = models.CharField(max_length=24)
    contact = models.ManyToManyField(Contact)
    url = models.ManyToManyField(URL_i18n)
    ts = models.DateTimeField(auto_now=True)

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