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
from django.utils import six
from edumanage.models import *
from lxml.etree import parse
from collections import defaultdict
import argparse
import sys
import traceback
import re


class Command(BaseCommand):
    help = '''
    Parses an institution XML file and creates institution,
    institution realm, contact and service location entries
    '''
    # leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('file', type=argparse.FileType('r'),
                            nargs='?', default=sys.stdin)
        parser.add_argument('--strict-empty-text-nodes',
                            dest='strict',
                            action='store_true',
                            default=False,
                            help='''Parse empty text nodes as None instead of an
empty string. This will break if a target field does not accept null values, but
it is useful if you want to enforce that the input XML aligns with the database
schema.''')
        parser.add_argument(
            '--eduroam-database-version',
            dest='edb_version',
            type=int,
            default=2
        )

    def handle(self, **options):
        '''
        Handle command
        '''

        if int(options['verbosity']) > 0:
            self.stdout.write_maybe = self.stdout.write
        else:
            self.stdout.write_maybe = lambda *args: None

        self.strict_empty_text_nodes = options['strict']

        self.edb_version = options['edb_version']

        self.parse_and_create(options['file'])

    def parse_and_create(self, instxmlfile):
        try:
            doc = parse(instxmlfile)
        except:
            raise CommandError('%s\n%s' % (
                  '%s does not exist or it could not be read/parsed' %
                  instxmlfile,
                  traceback.format_exc()
                  ))
        try:
            self.nrorealm = Realm.objects.get(country=settings.NRO_COUNTRY_CODE)
        except (Realm.DoesNotExist, AttributeError):
            raise CommandError('%s\n%s' % (
                  'Failed to get the Realm object',
            '''Before running this command, the following prerequisites must be met:
- NRO_COUNTRY_CODE and REALM_COUNTRIES must be configured in settings
- a Realm object must be added, matching the NRO_COUNTRY_CODE'''))
        root = doc.getroot()
        institution_list = []
        institutions = root.getchildren()
        self.stdout.write_maybe('Walking %s' % root.tag)
        for institution in institutions:
            institution_obj = self.parse_and_create_institution(institution)
            institution_list.append(institution_obj)
        return True

    def parse_and_create_name(self, relobj_or_model, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        try:
            parameters = {
                'lang': element.attrib['lang'],
                'name': self.parse_text_node(element)
                }
        except:
            self.stdout.write_maybe('Skipping %s: invalid' % element.tag)
            return (None, False)
        for key in parameters:
            if not parameters[key]:
                self.stdout.write_maybe('Skipping %s: empty %s' %
                                        (element.tag, key))
                return (None, False)
        try:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(type(relobj_or_model))
            parameters['object_id'] = relobj_or_model.pk
            bound = True
        # (ModelClass) object has no attribute '_meta'
        except AttributeError:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(relobj_or_model)
            bound = False
        object_tuple = Name_i18n.objects.get_or_create(**parameters)
        created_or_found = 'Created' if object_tuple[1] else 'Found'
        if object_tuple[1] and not bound:
            created_or_found += ' (preliminary)'
        self.stdout.write_maybe('%s %s: %s' %
                                (created_or_found,
                                 type_str(object_tuple[0]),
                                six.text_type(object_tuple[0])))
        return object_tuple

    def parse_and_create_address(self, relobj_or_model, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        parameters = {}
        required_parameters = ['lang', 'street', 'city']
        for child_element in element.getchildren():
            try:
                lang = element.attrib['lang']
                if 'lang' in parameters:
                    assert lang == parameters['lang']
                else:
                    parameters['lang'] = lang
            except KeyError:
                self.stdout.write_maybe('Skipping %s: invalid' % element.tag)
                return None, False
            except AssertionError:
                self.stdout.write_maybe(
                    'Skipping %s: different languages not supported' %
                    element.tag
                )
                return None, False
            parameters[child_element.tag] = \
                self.parse_text_node(child_element)
        if not all([key in parameters for key in required_parameters]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None, False
        if not all([key in required_parameters for key in parameters]):
            self.stdout.write_maybe('Skipping %s: invalid' % element.tag)
            return None, False
        for key in parameters:
            if not parameters[key]:
                self.stdout.write_maybe('Skipping %s: empty %s' %
                                        (element.tag, key))
                return None, False
        try:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(type(relobj_or_model))
            parameters['object_id'] = relobj_or_model.pk
            bound = True
        # (ModelClass) object has no attribute '_meta'
        except AttributeError:
            parameters['content_type'] = \
              ContentType.objects.get_for_model(relobj_or_model)
            bound = False
        object_tuple = Address_i18n.objects.get_or_create(**parameters)
        created_or_found = 'Created' if object_tuple[1] else 'Found'
        if object_tuple[1] and not bound:
            created_or_found += ' (preliminary)'
        self.stdout.write_maybe('%s %s: %s' %
                                (created_or_found,
                                 type_str(object_tuple[0]),
                                 six.text_type(object_tuple[0])))
        return object_tuple

    def parse_and_create_url(self, relobj, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        try:
            parameters = {
                'lang':    element.attrib['lang'],
                'url':     self.parse_text_node(element),
                'urltype': element.tag.replace('_URL', ''),
                }
        except:
            self.stdout.write_maybe('Skipping %s: invalid' % element.tag)
            return (None, False)
        for key in parameters:
            if not parameters[key]:
                self.stdout.write_maybe('Skipping %s: empty %s' %
                                        (element.tag, key))
                return (None, False)
        parameters.update({
            'object_id': relobj.pk,
            'content_type': ContentType.objects.get_for_model(type(relobj))
            })
        obj, obj_created = URL_i18n.objects.get_or_create(**parameters)
        self.stdout.write_maybe('%s %s: %s' %
                                ('Created' if obj_created else 'Found',
                                 type_str(obj),
                                six.text_type(obj)))
        return obj

    def parse_and_create_instrealm(self, institution_obj, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        parameters = {
            'realm': self.parse_text_node(element),
            'instid': institution_obj
            }
        if not parameters['realm']:
            self.stdout.write_maybe('Skipping %s: invalid realm' % element.tag)
            return (None, False)
        object_tuple = InstRealm.objects.get_or_create(**parameters)
        self.stdout.write_maybe('%s %s: %s' %
                                ('Created' if object_tuple[1] else 'Found',
                                 type_str(object_tuple[0]),
                                six.text_type(object_tuple[0])))
        return object_tuple

    def parse_and_create_contact(self, relobj, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        parameters = {}
        for child_element in element.getchildren():
            if child_element.tag in ['name', 'email', 'phone']:
                parameters[child_element.tag] = \
                    self.parse_text_node(child_element)
        if not 'name' in parameters or not parameters['name']:
            self.stdout.write_maybe('Skipping %s: invalid name' % element.tag)
            return None
        if isinstance(relobj, Institution):
            #### revisit this vs. defaults=... +
            parameters['institutioncontactpool__institution'] = relobj
        elif isinstance(relobj, ServiceLoc):
            parameters['institutioncontactpool__institution'] = \
            relobj.institutionid
        else:
            self.stdout.write_maybe('Skipping %s: invalid argument %s' %
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
        self.stdout.write_maybe('%s %s: %s' %
                                ('Created' if obj_created else 'Found',
                                 type_str(obj),
                                six.text_type(obj)))
        return obj

    def parse_and_create_serviceloc(self, instobj, element):
        self.stdout.write_maybe('Walking %s' % element.tag)
        name_elements = []
        contact_elements = []
        url_elements = []
        address_elements = []
        parameters = {
            'AP_no': 0,
            'tag': [],
        }
        if self.edb_version == 1:
            edb_v1_tags = ['port_restrict', 'transp_proxy', 'IPv6', 'NAT']
            coordinates = defaultdict(list)
        else:
            coordinates = []
        coordinate_fields = [f.name for f in Coordinates._meta.get_fields()
                             if not f.auto_created]
        for child_element in element.getchildren():
            tag = child_element.tag
            self.stdout.write_maybe('- %s' % tag)
            if self.edb_version == 1 and tag in coordinate_fields[:2]:
                coordinates[tag].append(
                    self.parse_text_node(child_element)
                )
                continue
            if self.edb_version != 1 and tag == 'coordinates':
                for coord in self.parse_text_node(child_element).split(';'):
                    coordinates.append({
                        k: v for k, v in
                        zip(coordinate_fields, coord.split(',', 2))
                    })
                continue
            if tag == 'SSID':
                parameters[tag] = self.parse_text_node(child_element)
                continue
            if tag == 'loc_name':
                name_elements.append(child_element)
                continue
            if tag == 'contact':
                contact_elements.append(child_element)
                continue
            if tag == 'address':
                if self.edb_version == 1:
                    for sub_element in child_element.getchildren():
                        sub_element.attrib['lang'] = 'en'
                address_elements.append(child_element)
                continue
            if tag == 'enc_level':
                parameters['enc_level'] = \
                    self.parse_multi_value_text_node(child_element)
                continue
            if self.edb_version == 1 and tag == 'wired':
                parameters['wired_no'] = \
                    getattr(settings, '_SERVICELOC_DERIVE_WIRED_NO').get(
                        child_element.text in ('true', '1')
                    )
                continue
            if self.edb_version == 1 and tag in edb_v1_tags:
                if child_element.text in ('true', '1'):
                    parameters['tag'].append(tag)
                continue
            if self.edb_version != 1 and tag == 'tag':
                parameters[tag] = \
                    self.parse_multi_value_text_node(child_element)
                continue
            if tag == 'AP_no':
                parameters['AP_no'] = \
                  int(child_element.text)
                continue
            if self.edb_version != 1 and tag == 'wired_no':
                parameters[tag] = int(child_element.text)
                continue
            if tag == 'info_URL':
                url_elements.append(child_element)
        parameters['tag'] = sorted(set(parameters['tag']))
        self.stdout.write_maybe('Done walking %s' % element.tag)

        # abort if required data not present
        required_tags = ['SSID']
        if self.edb_version == 1:
            required_tags.append('enc_level')
        if not all([tag in parameters for tag in required_tags]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None
        if self.edb_version == 1 and len(address_elements) > 1:
            self.stdout.write_maybe('Skipping %s: invalid multiple addresses' %
                                    element.tag)
            return None
        if self.edb_version == 1 and not all(
                [len(coordinates[k] == 1) for k in coordinate_fields[:2]]
        ):
            self.stdout.write_maybe('Skipping %s: invalid longitude/latitude' %
                                    element.tag)
            return None
        if self.edb_version != 1 and len(coordinates) > 1:
            self.stdout.write_maybe('Skipping %s: multiple coordinates not '
                                    'supported currently' %
                                    element.tag)
            return None
        if self.edb_version != 1 and not all(
                [2 <= len(coord) <= 3 for coord in coordinates]
        ):
            self.stdout.write_maybe('Skipping %s: invalid coordinates' %
                                    element.tag)
            return None
        parameters['institutionid'] = instobj
        if self.edb_version == 1:
            coordinates = [{k: coordinates[k][0] for k in coordinates}]
        # try to find "identical" ServiceLoc (based on own fields)
        existing_obj = ServiceLoc.objects.filter(**parameters).\
          prefetch_related('loc_name')
        # chain filter for coordinates (lat, lon, alt)
        for term in [
                {'coordinates__{}'.format(k): coord[k] for k in coord}
                for coord in coordinates
        ]:
            existing_obj = existing_obj.filter(**term)
        # Prepare list of unique loc_name's for the location we are parsing.
        # Don't use self.parse_and_create_name(ServiceLoc, name_element)
        # as it may find existing Name_i18n objects by the same name, but
        # unrelated to this location; also we'd rather not create Name_i18n
        # objects that may go away after all
        names_new = set([self.parse_text_node(name_element)
                         for name_element in name_elements])
        # No ServiceLoc objects matching these parameters
        if not existing_obj.exists():
            obj_created = True
        else:
            # Extend the comparison to the names (their set vs. our set)
            # for each matched ServiceLoc
            for obj in existing_obj:
                names_old = set(obj.loc_name.all().\
                                values_list('name', flat=True))
                # If an exact match is found, stop here;
                # obj is the existing ServiceLoc
                if names_old == names_new:
                    obj_created = False
                    break
            # Finally if no match, let's create a new ServiceLoc
            else:
                obj_created = True
        if obj_created:
            obj = ServiceLoc(**parameters)
            obj.save()
            for name_element in name_elements:
                self.parse_and_create_name(obj, name_element)
        self.stdout.write_maybe('%s %s: %s' %
                                ('Created' if obj_created else 'Found',
                                 type_str(obj),
                                six.text_type(obj)))
        if obj_created:
            for coord in coordinates:
                cobj, cobj_created = \
                    obj.coordinates.get_or_create(**coord)
                self.stdout.write_maybe('%s %s: %s' %
                                        ('Created' if cobj_created
                                         else 'Found',
                                         type_str(cobj),
                                         six.text_type(cobj)))
        for address_element in address_elements:
            self.parse_and_create_address(obj, address_element)
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
            self.stdout.write_maybe('Linked %s contacts: %s' % (
                type_str(obj),
                ' '.join([six.text_type(c) for c in contacts_add])
                ))
        contacts_remove = set(contacts_db) - set(contacts_new)
        for c in contacts_remove:
            # c.delete()
            obj.contact.remove(c)
        if len(contacts_remove) > 0:
            self.stdout.write_maybe('Removed %s contacts: %s' % (
                type_str(obj),
                ' '.join([six.text_type(c) for c in contacts_remove])
                ))
        return obj

    def parse_and_create_institution(self, element):
        self.stdout.write_maybe('Walking %s' % element.tag)
        parameters = {}
        # parameters['number_id'] = 1
        coordinate_fields = [f.name for f in Coordinates._meta.get_fields()
                             if not f.auto_created]
        name_tag = 'org_name' if self.edb_version == 1 else 'inst_name'
        for child_element in element.getchildren():
            tag = child_element.tag
            self.stdout.write_maybe('- %s' % tag)
            # hardcode to self.nrorealm, ignore country
            if tag == 'country':
                continue
            if tag == 'type':
                if self.edb_version == 1:
                    parameters[tag] = int(child_element.text)
                else:
                    parameters[tag] = get_ertype_number(child_element.text)
                continue
            if tag in ['inst_realm', name_tag, 'contact',
                       'info_URL', 'policy_URL', 'location',
                       'address']:
                if tag == 'address' and self.edb_version == 1:
                    for sub_element in child_element.getchildren():
                        sub_element.attrib['lang'] = 'en'
                if not tag in parameters:
                    parameters[tag] = []
                parameters[tag].append(child_element)
                continue
            if self.edb_version != 1 and tag == 'coordinates':
                parameters[tag] = [
                    {k: v for k, v in
                     zip(coordinate_fields, coord.split(',', 2))}
                    for coord in self.parse_text_node(child_element).split(';')
                ]
        self.stdout.write_maybe('Done walking %s' % element.tag)

        # abort if required data not present
        required_tags = ['type', name_tag, 'info_URL', 'address']
        if not all([tag in parameters for tag in required_tags]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None
        if self.edb_version == 1 and len(parameters['address']) > 1:
            self.stdout.write_maybe('Skipping %s: invalid multiple addresses' %
                                    element.tag)
            return None
        if self.edb_version != 1 and parameters.get('coordinates', []):
            if len(parameters['coordinates']) != 1:
                self.stdout.write_maybe('Skipping %s: invalid multiple '
                                        'coordinates' % element.tag)
                return None
            if not all([2 <= len(coord) <= 3
                        for coord in parameters['coordinates']]):
                self.stdout.write_maybe('Skipping %s: invalid coordinates' %
                                        element.tag)
                return None
        if parameters['type'] not in [1, 2, 3]:
            self.stdout.write_maybe('Skipping %s: invalid type %d' %
                                    (element.tag,
                                     parameters['type']))
            return None
        if parameters['type'] != 2 and 'inst_realm' not in parameters:
            self.stdout.write_maybe('Skipping %s: type %d but no "inst_realm"' %
                                    (element.tag,
                                     parameters['type']))
            return None
        if parameters['type'] != 1 and 'location' not in parameters:
            self.stdout.write_maybe('Skipping %s: type %d but no "location"' %
                                    (element.tag,
                                     parameters['type']))
            return None

        for idx, name_element in enumerate(parameters[name_tag]):
            parameters[name_tag][idx] = \
              self.parse_and_create_name(Institution, name_element)
        if [True] * len(parameters[name_tag]) == [x[1] for x in
                                                     parameters[name_tag]]:
            institution_obj = Institution(realmid=self.nrorealm,
                                          ertype=parameters['type'])
            institution_obj.save()
            for name, created in parameters[name_tag]:
                name.content_object = institution_obj
                name.save()
            self.stdout.write_maybe('%s %s: %s' %
                                    ('Created',
                                     type_str(institution_obj),
                                    six.text_type(institution_obj)))
        else:
            institution_obj = parameters[name_tag][0][0].content_object
            if institution_obj is None:
                raise Exception(
                    'The following institution names were found but they ' +
                    'are not associated with an institution (only tried the ' +
                    'first one)! This must be fixed (e.g. by removing ' +
                    'duplicate objects) before we can proceed.\n' +
                    '\n'.join([six.text_type(x[0]) for x in parameters[name_tag]])
                    )
            if not [institution_obj] * len(parameters[name_tag]) == \
              [getattr(x[0], 'content_object')
               for x in parameters[name_tag]]:
                raise Exception(
                    'The following institution names were found but they ' +
                    'are not associated with the same institution. ' +
                    'This must be fixed (e.g. by removing duplicate objects) ' +
                    'before we can proceed.\n' +
                    '\n'.join([six.text_type(x[0]) for x in parameters[name_tag]])
                    )
            self.stdout.write_maybe('%s %s: %s' %
                                    ('Found',
                                     type_str(institution_obj),
                                    six.text_type(institution_obj)))

        for idx, contact_element in enumerate(parameters['contact']):
            parameters['contact'][idx] = \
              self.parse_and_create_contact(institution_obj, contact_element)
        instdetails_defaults = [
            # 'number_id',
        ]
        instdetails_defaults = {x: parameters[x] for x in instdetails_defaults}
        instdetails_obj, instdetails_created = \
          InstitutionDetails.objects.\
          get_or_create(defaults=instdetails_defaults,
                        institution=institution_obj)
        if not instdetails_created:
            for attr in instdetails_defaults:
                setattr(instdetails_obj, attr, instdetails_defaults[attr])
        self.stdout.write_maybe('%s %s: %s' %
                                ('Created' if instdetails_created else 'Found',
                                 type_str(instdetails_obj),
                                six.text_type(instdetails_obj)))

        contacts_db = instdetails_obj.contact.all()
        contacts_add = set(parameters['contact']) - set(contacts_db)
        for c in contacts_add:
            instdetails_obj.contact.add(c)
        if len(contacts_add) > 0:
            self.stdout.write_maybe('Linked %s contacts: %s' % (
                type_str(instdetails_obj),
                ' '.join([six.text_type(c) for c in contacts_add])
                ))
        contacts_remove = set(contacts_db) - set(parameters['contact'])
        for c in contacts_remove:
            # c.delete()
            instdetails_obj.contact.remove(c)
        if len(contacts_remove) > 0:
            self.stdout.write_maybe('Removed %s contacts: %s' % (
                type_str(instdetails_obj),
                ' '.join([six.text_type(c) for c in contacts_remove])
                ))

        for tag in ['info_URL', 'policy_URL']:
            if tag in parameters:
                for url_element in parameters[tag]:
                    url_obj = \
                      self.parse_and_create_url(instdetails_obj, url_element)

        for idx, address_element in enumerate(parameters['address']):
            parameters['address'][idx] = \
                self.parse_and_create_address(
                    instdetails_obj, address_element)

        for idx, coord in enumerate(parameters['coordinates']):
            cobj, cobj_created = \
                instdetails_obj.coordinates.get_or_create(**coord)
            self.stdout.write_maybe('%s %s: %s' %
                                    ('Created' if cobj_created
                                     else 'Found',
                                     type_str(cobj),
                                     six.text_type(cobj)))
            parameters['coordinates'][idx] = (cobj, cobj_created)

        for idx, instrealm_element in enumerate(parameters.get('inst_realm', [])):
            parameters['inst_realm'][idx] = \
              self.parse_and_create_instrealm(institution_obj,
                                              instrealm_element)

        for idx, serviceloc_element in enumerate(parameters.get('location', [])):
            parameters['location'][idx] = \
              self.parse_and_create_serviceloc(institution_obj,
                                               serviceloc_element)

        return institution_obj

    def parse_text_node(self, node, **kwargs):
        return_none_on_empty = kwargs.get('strict') if 'strict' in kwargs \
            else self.strict_empty_text_nodes
        if hasattr(node.text, 'strip') and callable(node.text.strip):
            return node.text.strip()
        elif node.text is None and not return_none_on_empty:
            return ''
        else:
            return None

    def parse_multi_value_text_node(self, *args, **kwargs):
        value = self.parse_text_node(*args, **kwargs)
        value = re.split(r'\s*,\s*', value)
        return sorted(set(value))

def type_str(obj):
    return type(obj).__name__
