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
from django.conf import settings
from edumanage.models import *
from lxml.etree import parse
import sys
import traceback
import re


class Command(BaseCommand):
    help = '''
    Parses an institution XML file and creates institution,
    institution realm, contact and service location entries
    '''
    args = '<file>'

    # leave_locale_alone = True

    def handle(self, *args, **options):
        '''
        Handle command
        '''

        if args is None or len(args) != 1:
            raise CommandError('You must supply a file name')

        if int(options['verbosity']) > 0:
            self.real_write = self.stdout.write
        else:
            self.real_write = lambda *args: None

        self.parse_and_create(args[0])

    def parse_and_create(self, instxmlfile):
        try:
            doc = parse(instxmlfile)
        except:
            self.stderr.\
              write('ERROR: %s\n%s' % (
                  '%s does not exist or it could not be read/parsed' %
                  instxmlfile,
                  traceback.format_exc()
                  ))
            sys.exit(1)
        try:
            self.nrorealm = Realm.objects.get(country=settings.NRO_COUNTRY_CODE)
        except Realm.DoesNotExist, AttributeError:
            self.stderr.\
              write('ERROR: %s\n%s' % (
                  'Failed to get the Realm object',
            '''Before running this command, the following prerequisites must be met:
- NRO_COUNTRY_CODE and REALM_COUNTRIES must be configured in settings
- a Realm object must be added, matching the NRO_COUNTRY_CODE'''))
            sys.exit(1)
        root = doc.getroot()
        institution_list = []
        institutions = root.getchildren()
        self.real_write('Walking %s' % root.tag)
        for institution in institutions:
            institution_obj = self.parse_and_create_institution(institution)
            institution_list.append(institution_obj)
        return True

    def parse_and_create_name(self, relobj_or_model, element):
        self.real_write('Parsing %s' % element.tag)
        try:
            parameters = {
                'lang': element.attrib['lang'],
                'name': element.text
                }
        except:
            self.real_write('Skipping %s: invalid' % element.tag)
            return (None, False)
        for key in parameters:
            if not parameters[key]:
                self.real_write('Skipping %s: empty %s' %
                                (element.tag, key))
                return (None, False)
        try:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(type(relobj_or_model))
            parameters['object_id'] = relobj_or_model.pk
        # (ModelClass) object has no attribute '_meta'
        except AttributeError:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(relobj_or_model)
        object_tuple = Name_i18n.objects.get_or_create(**parameters)
        self.real_write('%s %s: %s' %
                        ('Created' if object_tuple[1] else 'Found',
                             type_str(object_tuple[0]),
                             unicode(object_tuple[0])))
        return object_tuple

    def parse_and_create_url(self, relobj, element):
        self.real_write('Parsing %s' % element.tag)
        try:
            parameters = {
                'lang':    element.attrib['lang'],
                'url':     element.text,
                'urltype': element.tag.replace('_URL', ''),
                }
        except:
            self.real_write('Skipping %s: invalid' % element.tag)
            return (None, False)
        for key in parameters:
            if not parameters[key]:
                self.real_write('Skipping %s: empty %s' %
                                (element.tag, key))
                return (None, False)
        parameters.update({
            'object_id': relobj.pk,
            'content_type': ContentType.objects.get_for_model(type(relobj))
            })
        obj, obj_created = URL_i18n.objects.get_or_create(**parameters)
        self.real_write('%s %s: %s' %
                        ('Created' if obj_created else 'Found',
                             type_str(obj),
                             unicode(obj)))
        return obj

    def parse_and_create_instrealm(self, institution_obj, element):
        self.real_write('Parsing %s' % element.tag)
        parameters = {
            'realm': element.text,
            'instid': institution_obj
            }
        if not parameters['realm']:
            self.real_write('Skipping %s: invalid realm' % element.tag)
            return (None, False)
        object_tuple = InstRealm.objects.get_or_create(**parameters)
        self.real_write('%s %s: %s' %
                        ('Created' if object_tuple[1] else 'Found',
                             type_str(object_tuple[0]),
                             unicode(object_tuple[0])))
        return object_tuple

    def parse_and_create_contact(self, relobj, element):
        self.real_write('Parsing %s' % element.tag)
        parameters = {}
        for child_element in element.getchildren():
            if child_element.tag in ['name', 'email', 'phone']:
                parameters[child_element.tag] = child_element.text
        if not 'name' in parameters and not parameters['name']:
            self.real_write('Skipping %s: invalid name' % element.tag)
            return None
        if isinstance(relobj, Institution):
            #### revisit this vs. defaults=... +
            parameters['institutioncontactpool__institution'] = relobj
        elif isinstance(relobj, ServiceLoc):
            parameters['institutioncontactpool__institution'] = \
            relobj.institutionid
        else:
            self.real_write('Skipping %s: invalid argument %s' %
                            (element.tag,
                             relobj))
            return None
        instobj = parameters['institutioncontactpool__institution']
        obj, obj_created = \
          Contact.objects.get_or_create(**parameters)
        if obj_created or \
          not hasattr(obj, 'institutioncontactpool'):
            contactpool_obj, contactpool_obj_created = \
              InstitutionContactPool.objects.\
              get_or_create(contact=obj, institution=instobj)
        self.real_write('%s %s: %s' %
                        ('Created' if obj_created else 'Found',
                             type_str(obj),
                             unicode(obj)))
        return obj

    def parse_and_create_serviceloc(self, instobj, element):
        self.real_write('Walking %s' % element.tag)
        name_elements = []
        contact_elements = []
        url_elements = []
        # eduroam db XSD says these are optional, but unfortunately
        # they are not optional in our schema, so use some defaults
        parameters = {k : False for k in ['port_restrict', 'transp_proxy',
                                          'IPv6', 'NAT', 'wired']}
        parameters['AP_no'] = 0
        for child_element in element.getchildren():
            tag = child_element.tag
            self.real_write('- %s' % tag)
            if tag in ['longitude', 'latitude', 'SSID']:
                parameters[tag] = child_element.text
                continue
            if tag == 'loc_name':
                name_elements.append(child_element)
                continue
            if tag == 'contact':
                contact_elements.append(child_element)
                continue
            if tag == 'address':
                for sub_element in child_element.getchildren():
                    if sub_element.tag in ['street', 'city']:
                        parameters['address_' + sub_element.tag] = \
                          sub_element.text
                continue
            if tag == 'enc_level':
                parameters['enc_level'] = \
                  re.split(r'\s*,\s*', child_element.text)
                continue
            if tag in ['port_restrict', 'transp_proxy',
                       'IPv6', 'NAT', 'wired']:
                parameters[tag] = \
                  child_element.text in ('true', '1')
                continue
            if tag == 'AP_no':
                parameters['AP_no'] = \
                  int(child_element.text)
                continue
            if tag == 'info_URL':
                url_elements.append(child_element)
        self.real_write('Done walking %s' % element.tag)

        # abort if required data not present
        if False in [x in parameters
                     for x in ['longitude', 'latitude',
                               'address_street', 'address_city',
                               'SSID', 'enc_level']]:
            self.real_write('Skipping %s: incomplete' % element.tag)
            return None
        parameters['institutionid'] = instobj
        obj, obj_created = \
          ServiceLoc.objects.\
          get_or_create(**parameters)
        self.real_write('%s %s: %s' %
                        ('Created' if obj_created else 'Found',
                         type_str(obj),
                         unicode(obj)))
        for name_element in name_elements:
            self.parse_and_create_name(obj, name_element)
        for url_element in url_elements:
            self.parse_and_create_url(obj, url_element)
        contacts_new = []
        for contact_element in contact_elements:
            contactobj = self.parse_and_create_contact(obj, contact_element)
            if contactobj is not None:
                contacts_new.append(contactobj)
        contacts_db = obj.contact.all()
        contacts_add = set(contacts_new) - set(contacts_db)
        for c in contacts_add:
            obj.contact.add(c)
        if len(contacts_add) > 0:
            self.real_write('Linked %s contacts: %s' % (
                type_str(obj),
                ' '.join([unicode(c) for c in contacts_add])
                ))
        contacts_remove = set(contacts_db) - set(contacts_new)
        for c in contacts_remove:
            # c.delete()
            obj.contact.remove(c)
        if len(contacts_remove) > 0:
            self.real_write('Removed %s contacts: %s' % (
                type_str(obj),
                ' '.join([unicode(c) for c in contacts_remove])
                ))
        return obj

    def parse_and_create_institution(self, element):
        self.real_write('Walking %s' % element.tag)
        parameters = {}
        # parameters['number_id'] = 1
        for child_element in element.getchildren():
            tag = child_element.tag
            self.real_write('- %s' % tag)
            # hardcode to self.nrorealm, ignore country
            if tag == 'country':
                continue
            if tag == 'type':
                parameters[tag] = int(child_element.text)
                continue
            if tag in ['inst_realm', 'org_name', 'contact',
                       'info_URL', 'policy_URL', 'location']:
                if not tag in parameters:
                    parameters[tag] = []
                parameters[tag].append(child_element)
                continue
            if tag == 'address':
                for sub_element in child_element.getchildren():
                    if sub_element.tag in ['street', 'city']:
                        parameters['address_' + sub_element.tag] = \
                          sub_element.text
        self.real_write('Done walking %s' % element.tag)

        # abort if required data not present
        if False in \
          [x in parameters
           for x in ['type', 'org_name',
                     'address_street', 'address_city',
                     'info_URL']]:
            self.real_write('Skipping %s: incomplete' % element.tag)
            return None
        if parameters['type'] not in [1, 2, 3]:
            self.real_write('Skipping %s: invalid type %d' %
                            (element.tag,
                             parameters['type']))
            return None
        if parameters['type'] != 2 and 'inst_realm' not in parameters:
            self.real_write('Skipping %s: type %d but no "inst_realm"' %
                            (element.tag,
                             parameters['type']))
            return None
        if parameters['type'] != 1 and 'location' not in parameters:
            self.real_write('Skipping %s: type %d but no "location"' %
                            (element.tag,
                             parameters['type']))
            return None

        for idx, name_element in enumerate(parameters['org_name']):
            parameters['org_name'][idx] = \
              self.parse_and_create_name(Institution, name_element)
        if [True] * len(parameters['org_name']) == [x[1] for x in
                                                     parameters['org_name']]:
            institution_obj = Institution(realmid=self.nrorealm,
                                          ertype=parameters['type'])
            institution_obj.save()
            for name, created in parameters['org_name']:
                name.content_object = institution_obj
                name.save()
            self.real_write('%s %s: %s' %
                            ('Created',
                             type_str(institution_obj),
                             unicode(institution_obj)))
        else:
            institution_obj = parameters['org_name'][0][0].content_object
            if institution_obj is None:
                raise Exception(
                    'The following institution names were found but they ' +
                    'are not associated with an institution (only tried the ' +
                    'first one)! This must be fixed (e.g. by removing ' +
                    'duplicate objects) before we can proceed.\n' +
                    '\n'.join([unicode(x[0]) for x in parameters['org_name']])
                    )
            if not [institution_obj] * len(parameters['org_name']) == \
              [getattr(x[0], 'content_object')
               for x in parameters['org_name']]:
                raise Exception(
                    'The following institution names were found but they ' +
                    'are not associated with the same institution. ' +
                    'This must be fixed (e.g. by removing duplicate objects) ' +
                    'before we can proceed.\n' +
                    '\n'.join([unicode(x[0]) for x in parameters['org_name']])
                    )
            self.real_write('%s %s: %s' %
                            ('Found',
                             type_str(institution_obj),
                             unicode(institution_obj)))

        for idx, contact_element in enumerate(parameters['contact']):
            parameters['contact'][idx] = \
              self.parse_and_create_contact(institution_obj, contact_element)
        instdetails_defaults={x: parameters[x]
                              for x in ['address_street',
                                        'address_city']}
                                        # 'number_id']
        instdetails_obj, instdetails_created = \
          InstitutionDetails.objects.\
          get_or_create(defaults=instdetails_defaults,
                        institution=institution_obj)
        if not instdetails_created:
            for attr in instdetails_defaults:
                setattr(instdetails_obj, attr, instdetails_defaults[attr])
        self.real_write('%s %s: %s' %
                        ('Created' if instdetails_created else 'Found',
                         type_str(instdetails_obj),
                         unicode(instdetails_obj)))

        contacts_db = instdetails_obj.contact.all()
        contacts_add = set(parameters['contact']) - set(contacts_db)
        for c in contacts_add:
            instdetails_obj.contact.add(c)
        if len(contacts_add) > 0:
            self.real_write('Linked %s contacts: %s' % (
                type_str(instdetails_obj),
                ' '.join([unicode(c) for c in contacts_add])
                ))
        contacts_remove = set(contacts_db) - set(parameters['contact'])
        for c in contacts_remove:
            # c.delete()
            instdetails_obj.contact.remove(c)
        if len(contacts_remove) > 0:
            self.real_write('Removed %s contacts: %s' % (
                type_str(instdetails_obj),
                ' '.join([unicode(c) for c in contacts_remove])
                ))

        for tag in ['info_URL', 'policy_URL']:
            if tag in parameters:
                for url_element in parameters[tag]:
                    url_obj = \
                      self.parse_and_create_url(instdetails_obj, url_element)

        for idx, instrealm_element in enumerate(parameters['inst_realm']):
            parameters['inst_realm'][idx] = \
              self.parse_and_create_instrealm(institution_obj,
                                              instrealm_element)

        for idx, serviceloc_element in enumerate(parameters['location']):
            parameters['location'][idx] = \
              self.parse_and_create_serviceloc(institution_obj,
                                               serviceloc_element)

        return institution_obj

def type_str(obj):
    return type(obj).__name__
