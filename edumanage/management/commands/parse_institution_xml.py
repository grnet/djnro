# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

# Copyright © 2011-2015 Greek Research and Technology Network (GRNET S.A.)
#
# Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr),
# Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr) and Stavros Kroustouris
# (staurosk-at-noc-dot-grnet-dot-gr), GRNET NOC
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
from django.core.management.base import BaseCommand, CommandError
from edumanage.models import *
from xml.etree import ElementTree
import sys


class Command(BaseCommand):
    help = '''
    Parses an institution XML file and creates institution,
    institution realm, contact and service location entries
    '''
    args = '<file>'
    label = 'file name to be imported'

    def handle(self, *args, **options):
        '''
        Handle command
        '''

        if args is None or len(args) != 1:
            raise CommandError('You must supply a file name')

        if int(options['verbosity']) > 0:
            write = self.stdout.write
        else:
            write = lambda *args: None

        self.parse_and_create(args[0])

    def parse_and_create(self, instxmlfile):
        doc = ElementTree.parse(instxmlfile)
        realmid = Realm.objects.get(pk=1)
        root = doc.getroot()
        institutions = []
        institutions = root.getchildren()
        for institution in institutions:
            created_inst_details = False
            instcontactslist = []
            for instdetails in institution:
                write('Parsing: %s\n' % (instdetails.tag))
                if instdetails.tag == 'country':
                    continue
                if instdetails.tag == 'type':
                    type = instdetails.text
                    institution_obj = Institution(
                        realmid=realmid,
                        ertype=int(type)
                    )
                    institution_obj.save()
                    write('Created inst %s\n' % institution_obj.pk)
                    continue
                if instdetails.tag == 'inst_realm':
                    inst_realm = instdetails.text
                    inst_realm_obj = InstRealm(
                        realm=inst_realm,
                        instid=institution_obj
                    )
                    inst_realm_obj.save()
                    continue
                if instdetails.tag == 'org_name':
                    org_name_lang = instdetails.items()[0][1]
                    org_name = instdetails.text
                    t = Name_i18n(
                        content_object=institution_obj,
                        name=org_name,
                        lang=org_name_lang
                    )
                    t.save()
                    continue
                if instdetails.tag == 'address':
                    for address in instdetails.getchildren():
                        if address.tag == 'street':
                            street = address.text
                        if address.tag == 'city':
                            city = address.text
                    continue
                if instdetails.tag == 'contact':
                    for contact in instdetails.getchildren():
                        if contact.tag == 'name':
                            contact_name = contact.text
                        if contact.tag == 'email':
                            contact_email = contact.text
                        if contact.tag == 'phone':
                            contact_phone = contact.text
                    contact_obj = Contact(
                        name=contact_name,
                        email=contact_email,
                        phone=contact_phone
                    )
                    contact_obj.save()
                    instcontactslist.append(contact_obj)
                    institution_contact_obj = InstitutionContactPool(
                        contact=contact_obj,
                        institution=institution_obj
                    )
                    institution_contact_obj.save()
                    continue

                if not created_inst_details:
                    instdets_obj = InstitutionDetails(
                        institution=institution_obj,
                        address_street=street,
                        address_city=city,
                        number_id=1
                    )
                    print instcontactslist
                    instdets_obj.save()
                    instdets_obj.contact = instcontactslist
                    instdets_obj.save()
                    created_inst_details = True

                if instdetails.tag == 'info_URL':
                    info_url_lang = instdetails.items()[0][1]
                    info_url = instdetails.text
                    u = URL_i18n(
                        content_object=instdets_obj,
                        urltype='info',
                        lang=info_url_lang,
                        url=info_url
                    )
                    u.save()
                    continue
                if instdetails.tag == 'policy_URL':
                    policy_url_lang = instdetails.items()[0][1]
                    policy_url = instdetails.text
                    u = URL_i18n(
                        content_object=instdets_obj,
                        urltype='policy',
                        lang=policy_url_lang,
                        url=policy_url
                    )
                    u.save()
                    continue

                if instdetails.tag == 'location':
                    location_names_list = []
                    location_address_list = []
                    parsedLocation = False
                    for locationdets in instdetails.getchildren():
                        if locationdets.tag == 'longitude':
                            location_long = locationdets.text
                            continue
                        if locationdets.tag == 'latitude':
                            location_lat = locationdets.text
                            continue
                        if locationdets.tag == 'loc_name':
                            loc_name_dict = {}
                            loc_name_lang = locationdets.items()[0][1]
                            loc_name = locationdets.text
                            loc_name_dict['name'] = loc_name
                            loc_name_dict['lang'] = loc_name_lang
                            location_names_list.append(loc_name_dict)
                            continue
                        if locationdets.tag == 'address':
                            loc_addr_dict = {}
                            for locaddress in locationdets.getchildren():
                                if locaddress.tag == 'street':
                                    locstreet = locaddress.text
                                    loc_addr_dict['street'] = locstreet
                                if locaddress.tag == 'city':
                                    loccity = locaddress.text
                                    loc_addr_dict['city'] = loccity
                            location_address_list.append(loc_addr_dict)
                            continue
                        if locationdets.tag == 'SSID':
                            loc_ssid = locationdets.text
                            continue
                        if locationdets.tag == 'enc_level':
                            loc_enc_level = locationdets.text
                            continue
                        if locationdets.tag == 'port_restrict':
                            loc_port_restrict_txt = locationdets.text
                            loc_port_restrict = False
                            if loc_port_restrict_txt in ('true', '1'):
                                loc_port_restrict = True
                            continue
                        if locationdets.tag == 'transp_proxy':
                            loc_transp_proxy_txt = locationdets.text
                            loc_transp_proxy = False
                            if loc_transp_proxy_txt in ('true', '1'):
                                loc_transp_proxy = True
                            continue
                        if locationdets.tag == 'IPv6':
                            loc_ipv6_txt = locationdets.text
                            loc_ipv6 = False
                            if loc_ipv6_txt in ('true', '1'):
                                loc_ipv6 = True
                            continue
                        if locationdets.tag == 'NAT':
                            loc_nat_txt = locationdets.text
                            loc_nat = False
                            if loc_nat_txt in ('true', '1'):
                                loc_nat = True
                            continue
                        if locationdets.tag == 'AP_no':
                            loc_ap_no = int(locationdets.text)
                            continue
                        if locationdets.tag == 'wired':
                            loc_wired_txt = locationdets.text
                            loc_wired = False
                            if loc_wired_txt in ('true', '1'):
                                loc_wired = True
                        if not parsedLocation:
                            write('Creating location:\n')
                            try:
                                serviceloc = ServiceLoc(
                                    institutionid=institution_obj,
                                    longitude=location_long,
                                    latitude=location_lat,
                                    address_street=locstreet,
                                    address_city=loccity,
                                    SSID=loc_ssid,
                                    enc_level=loc_enc_level,
                                    port_restrict=loc_port_restrict,
                                    transp_proxy=loc_transp_proxy,
                                    IPv6=loc_ipv6,
                                    NAT=loc_nat,
                                    AP_no=loc_ap_no,
                                    wired=loc_wired
                                )
                                serviceloc.save()
                                for locat_name in location_names_list:
                                    t = Name_i18n(
                                        content_object=serviceloc,
                                        name=locat_name['name'],
                                        lang=locat_name['lang']
                                    )
                                    t.save()
                            except Exception as e:
                                write('ERROR: %s\n' % e)
                    continue
        return True
