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
from django.db.models.signals import post_save
from edumanage.models import *
from edumanage.views import ourPoints
from edumanage.signals import (
    disable_signals,
    DUID_RECACHE_OURPOINTS, DUID_SAVE_SERVICELOC_LATLON_CACHE
)
from lxml.etree import parse
from collections import defaultdict
import argparse
import sys
import traceback
import re
import uuid
import hashlib
from utils.edb_versioning import (
    EduroamDatabaseVersion, DEFAULT_EDUROAM_DATABASE_VERSION
)


class ParseInstitutionXMLError(Exception):
    pass
class ParseAddressError(ParseInstitutionXMLError):
    pass
class ParseNameError(ParseInstitutionXMLError):
    pass

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
            type=EduroamDatabaseVersion,
            default=DEFAULT_EDUROAM_DATABASE_VERSION,
            help='''eduroam database schema version to use for parsing input'''
        )
        parser.add_argument('--derive-uuids-with-md5',
                            dest='derive_uuids',
                            action='store_true',
                            default=True,
                            help='''Derive UUID values (for instid, locationid),
if necessary, by obtaining the hexdigest for the MD5 hash of the original value.
This returns 32 hex digits, which works as input for UUID.''')

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

        self.derive_uuids = options['derive_uuids']

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

    def parse_name(self, element):
        try:
            parameters = {
                'lang': element.attrib['lang'],
                'name': self.parse_text_node(element)
                }
        except KeyError:
            raise ParseNameError('invalid')
        for key in parameters:
            if not parameters[key]:
                raise ParseNameError('empty %s' % key)
        return parameters

    def parse_and_create_name(self, relobj_or_model, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        try:
            parameters = self.parse_name(element)
        except ParseNameError as pn_e:
            self.stdout.write_maybe('Skipping %s: %s' % (
                element.tag, pn_e))
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
        object_tuple = Name_i18n.objects.get_or_create(**parameters)
        created_or_found = 'Created' if object_tuple[1] else 'Found'
        if object_tuple[1] and not bound:
            created_or_found += ' (preliminary)'
        self.stdout.write_maybe('%s %s: %s' %
                                (created_or_found,
                                 type_str(object_tuple[0]),
                                six.text_type(object_tuple[0])))
        return object_tuple

    def parse_address(self, element):
        parameters = {}
        required_parameters = ['lang', 'street', 'city']
        for child_element in element.getchildren():
            try:
                lang = child_element.attrib['lang']
                if 'lang' in parameters:
                    assert lang == parameters['lang']
                else:
                    parameters['lang'] = lang
            except KeyError:
                raise ParseAddressError('invalid')
            except AssertionError:
                raise ParseAddressError(
                    'different languages not supported'
                )
            parameters[child_element.tag] = self.parse_text_node(child_element)
        if not all([key in parameters for key in required_parameters]):
            raise ParseAddressError('incomplete')
        if not all([key in required_parameters for key in parameters]):
            raise ParseAddressError('invalid')
        for key in parameters:
            if not parameters[key]:
                raise ParseAddressError('empty %s' % key)
        return parameters
    def parse_and_create_address(self, relobj_or_model, element):
        self.stdout.write_maybe('Parsing %s' % element.tag)
        try:
            parameters = self.parse_address(element)
        except ParseAddressError as pa_e:
            self.stdout.write_maybe('Skipping %s: %s' % (
                element.tag, pa_e))
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
        except KeyError:
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
        tags = ['name', 'email', 'phone']
        if self.edb_version.ge_version_2:
            tags += ['type', 'privacy']
        for child_element in element.getchildren():
            if child_element.tag in tags:
                parameters[child_element.tag] = \
                    self.parse_text_node(child_element)
        if not all([tag in parameters and parameters[tag] for tag in tags]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None
        if not all([tag in tags for tag in parameters]):
            self.stdout.write_maybe('Skipping %s: invalid' % element.tag)
            return None
        if isinstance(relobj, Institution):
            instobj = relobj
        elif isinstance(relobj, ServiceLoc):
            instobj = relobj.institutionid
        else:
            self.stdout.write_maybe('Skipping %s: invalid argument %s' %
                                    (element.tag,
                                     relobj))
            return None
        parameters['institutioncontactpool__institution'] = instobj
        # should matching also consider email, phone?
        id_parameters = {
            k: parameters.pop(k)
            for k in ['name', 'institutioncontactpool__institution']
            if k in parameters
        }
        obj, obj_created = Contact.objects.update_or_create(
            defaults=parameters,
            **id_parameters
        )
        if obj_created or not hasattr(obj, 'institutioncontactpool'):
            InstitutionContactPool.objects.get_or_create(
                contact=obj, institution=instobj)
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
        if self.edb_version.is_version_1:
            edb_v1_tags = ['port_restrict', 'transp_proxy', 'IPv6', 'NAT']
            coordinates = defaultdict(list)
        else:
            coordinates = []
        coordinate_fields = [f.name for f in Coordinates._meta.get_fields()
                             if not f.auto_created]
        serviceloc_field_map = {
            f.db_column: f.name
            for f in ServiceLoc._meta.get_fields()
            if f.db_column is not None and not f.auto_created
        }
        for child_element in element.getchildren():
            tag = child_element.tag
            self.stdout.write_maybe('- %s' % tag)
            if self.edb_version.ge_version_2 and tag == 'locationid':
                try:
                    parameters[tag] = \
                        self.parse_uuid_node(child_element)
                except ValueError as uuid_e:
                    self.stdout.write_maybe('Skipping %s: %s' % (
                        child_element.tag, uuid_e))
                continue
            if self.edb_version.ge_version_2 and tag in ('stage', 'type'):
                parameters[tag] = int(child_element.text)
                continue
            if self.edb_version.ge_version_2 and tag == 'location_type':
                parameters[tag] = self.parse_text_node(child_element)
                continue
            if self.edb_version.is_version_1 and tag in coordinate_fields[:2]:
                coordinates[tag].append(
                    self.parse_text_node(child_element)
                )
                continue
            if self.edb_version.ge_version_2 and tag == 'coordinates':
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
                if self.edb_version.is_version_1:
                    for sub_element in child_element.getchildren():
                        sub_element.attrib['lang'] = 'en'
                address_elements.append(child_element)
                continue
            if tag == 'enc_level':
                parameters[tag] = \
                    self.parse_multi_value_text_node(child_element)
                continue
            if self.edb_version.is_version_1 and tag == 'wired':
                parameters['wired_no'] = \
                    getattr(settings, 'SERVICELOC_DERIVE_WIRED_NO').get(
                        child_element.text in ('true', '1')
                    )
                continue
            if self.edb_version.is_version_1 and tag in edb_v1_tags:
                if child_element.text in ('true', '1'):
                    parameters['tag'].append(tag)
                continue
            if self.edb_version.ge_version_2 and tag == 'tag':
                parameters[tag] = \
                    self.parse_multi_value_text_node(child_element)
                continue
            if tag == 'AP_no':
                parameters[tag] = int(child_element.text)
                continue
            if self.edb_version.ge_version_2 and tag == 'wired_no':
                parameters[tag] = int(child_element.text)
                continue
            if tag == 'info_URL':
                url_elements.append(child_element)
        parameters['tag'] = sorted(set(parameters['tag']))
        self.stdout.write_maybe('Done walking %s' % element.tag)

        # abort if required data not present
        required_tags = ['SSID']
        if self.edb_version.is_version_1:
            required_tags.append('enc_level')
        else:
            required_tags += ['locationid', 'stage', 'type']
        if not all([tag in parameters for tag in required_tags]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None
        if self.edb_version.is_version_1 and len(address_elements) > 1:
            self.stdout.write_maybe('Skipping %s: invalid multiple addresses' %
                                    element.tag)
            return None
        if self.edb_version.is_version_1 and not all(
                [len(coordinates[k]) == 1 for k in coordinate_fields[:2]]
        ):
            self.stdout.write_maybe('Skipping %s: invalid longitude/latitude' %
                                    element.tag)
            return None
        if self.edb_version.ge_version_2 and not all(
                [2 <= len(coord) <= 3 for coord in coordinates]
        ):
            self.stdout.write_maybe('Skipping %s: invalid coordinates' %
                                    element.tag)
            return None
        if self.edb_version.ge_version_2 and len(coordinates) > 1:
            self.stdout.write_maybe('Transforming %s: multiple coordinates '
                                    'not supported currently, keeping the '
                                    'first one' %
                                    element.tag)
            coordinates = coordinates[:1]
        parameters = {
            serviceloc_field_map.get(k, k): parameters[k]
            for k in parameters
        }
        parameters['institutionid'] = instobj
        if self.edb_version.is_version_1:
            coordinates = [{k: coordinates[k][0] for k in coordinates}]

        id_parameters = ['institutionid']
        if self.edb_version.ge_version_2:
            id_parameters.append('locationid')
        id_parameters = {
            k: parameters[k]
            for k in id_parameters if k in parameters
        }
        # try to find "identical" ServiceLoc (based on subset of own fields)
        existing_obj = ServiceLoc.objects.filter(**id_parameters).\
          prefetch_related('loc_name')
        # for edb v1, chain filter for coordinates (lat, lon, alt)
        if not self.edb_version.ge_version_2:
            for term in [
                    {'coordinates__{}'.format(k): coord[k] for k in coord}
                    for coord in coordinates
            ]:
                existing_obj = existing_obj.filter(**term)
        if not self.edb_version.ge_version_2 and existing_obj.count() > 1:
            try:
                for term in [
                        {'loc_name__{}{}'.format(
                            k, '__bexact' if k == 'name' else ''): v
                         for k, v in self.parse_name(name_element).items()}
                        for name_element in name_elements
                ]:
                    existing_obj = existing_obj.filter(**term)
            except ParseNameError:
                pass
        if not self.edb_version.ge_version_2 and existing_obj.count() > 1:
            try:
                for term in [
                        {'address__{}{}'.format(
                            k, '__bexact' if k in ('street', 'city') else ''): v
                         for k, v in self.parse_address(address_element).items()}
                        for address_element in address_elements
                ]:
                    existing_obj = existing_obj.filter(**term)
            except ParseAddressError:
                pass
        try:
            obj = existing_obj.get()
            obj_created = False
        except ServiceLoc.DoesNotExist:
            obj_created = True
        # ServiceLoc.MultipleObjectsReturned not handled, should not happen at
        # this stage

        if obj_created:
            obj = ServiceLoc(**parameters)
            obj.save()
            for name_element in name_elements:
                self.parse_and_create_name(obj, name_element)
        else:
            parameters = {
                k: parameters[k] for k in parameters
                if k not in id_parameters
            }
            if parameters:
                for attr in parameters:
                    setattr(obj, attr, parameters[attr])
                obj.save()

        self.stdout.write_maybe(
            '%s %s: %s' % (
                'Created' if obj_created else 'Found',
                type_str(obj),
                six.text_type(obj)
            )
        )
        if obj_created:
            for coord in coordinates:
                cobj, cobj_created = \
                    obj.coordinates.get_or_create(**coord)
                self.stdout.write_maybe(
                    '%s %s: %s' % (
                        'Created' if cobj_created else 'Found',
                        type_str(cobj),
                        six.text_type(cobj)
                    )
                )
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
        if contacts_add:
            self.stdout.write_maybe('Linked %s contacts: %s' % (
                type_str(obj),
                ' '.join([six.text_type(c) for c in contacts_add])
                ))
        contacts_remove = set(contacts_db) - set(contacts_new)
        for c in contacts_remove:
            # c.delete()
            obj.contact.remove(c)
        if contacts_remove:
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
        field_map = {
            f.db_column: f.name
            for f in Institution._meta.get_fields() +
            InstitutionDetails._meta.get_fields()
            if getattr(f, 'db_column', None) is not None and not f.auto_created
        }
        name_tag = 'org_name' if self.edb_version.is_version_1 else 'inst_name'
        for child_element in element.getchildren():
            tag = child_element.tag
            self.stdout.write_maybe('- %s' % tag)
            if self.edb_version.ge_version_2 and tag == 'instid':
                try:
                    parameters[tag] = \
                        self.parse_uuid_node(child_element)
                except ValueError as uuid_e:
                    self.stdout.write_maybe('Skipping %s: %s' % (
                        child_element.tag, uuid_e))
                continue
            # hardcode to self.nrorealm, ignore country/ROid
            if self.edb_version.is_version_1 and tag == 'country':
                continue
            if self.edb_version.ge_version_2 and tag == "ROid":
                continue
            if tag == 'type':
                if self.edb_version.is_version_1:
                    parameters[tag] = int(child_element.text)
                else:
                    parameters[tag] = get_ertype_number(child_element.text)
                continue
            if self.edb_version.ge_version_2 and tag == 'stage':
                parameters[tag] = int(child_element.text)
                continue
            if self.edb_version.ge_version_2 and tag == 'inst_type':
                parameters[tag] = self.parse_text_node(child_element)
                continue
            if tag in ['inst_realm', name_tag, 'contact',
                       'info_URL', 'policy_URL', 'location',
                       'address']:
                if tag == 'address' and self.edb_version.is_version_1:
                    for sub_element in child_element.getchildren():
                        sub_element.attrib['lang'] = 'en'
                if not tag in parameters:
                    parameters[tag] = []
                parameters[tag].append(child_element)
                continue
            if self.edb_version.ge_version_2 and tag == 'coordinates':
                parameters[tag] = [
                    {k: v for k, v in
                     zip(coordinate_fields, coord.split(',', 2))}
                    for coord in self.parse_text_node(child_element).split(';')
                ]
        self.stdout.write_maybe('Done walking %s' % element.tag)

        # abort if required data not present
        required_tags = ['type', name_tag, 'info_URL', 'address']
        if self.edb_version.ge_version_2:
            required_tags += ['instid', 'stage']
        if not all([tag in parameters for tag in required_tags]):
            self.stdout.write_maybe('Skipping %s: incomplete' % element.tag)
            return None
        if self.edb_version.is_version_1 and len(parameters['address']) > 1:
            self.stdout.write_maybe('Skipping %s: invalid multiple addresses' %
                                    element.tag)
            return None
        if self.edb_version.ge_version_2 and parameters.get('coordinates', []):
            if len(parameters['coordinates']) != 1:
                self.stdout.write_maybe('Skipping %s: invalid multiple '
                                        'coordinates' % element.tag)
                return None
            if not all([2 <= len(coord) <= 3
                        for coord in parameters['coordinates']]):
                self.stdout.write_maybe('Skipping %s: invalid coordinates' %
                                        element.tag)
                return None
        if parameters['type'] not in ERTYPES:
            self.stdout.write_maybe('Skipping %s: invalid type %d' %
                                    (element.tag,
                                     parameters['type']))
            return None
        if parameters['type'] in ERTYPE_ROLES.IDP and 'inst_realm' not in parameters:
            self.stdout.write_maybe('Skipping %s: type %d but no "inst_realm"' %
                                    (element.tag,
                                     parameters['type']))
            return None
        if parameters['type'] in ERTYPE_ROLES.SP and 'location' not in parameters:
            self.stdout.write_maybe('Skipping %s: type %d but no "location"' %
                                    (element.tag,
                                     parameters['type']))
            return None

        parameters = {
            field_map.get(k, k): parameters[k]
            for k in parameters
        }
        try:
            institution_obj = Institution.objects.get(
                realmid=self.nrorealm, instid=parameters['instid']
            )
        except (Institution.DoesNotExist, KeyError):
            institution_obj = None
        for idx, name_element in enumerate(parameters[name_tag]):
            parameters[name_tag][idx] = \
                self.parse_and_create_name(
                    institution_obj if institution_obj is not None
                    else Institution,
                    name_element
                )
        if not institution_obj and all([
                created for _, created in parameters[name_tag]
        ]):
            institution_obj = Institution(realmid=self.nrorealm,
                                          ertype=parameters['ertype'])
            institution_obj.save()
            for name, _ in parameters[name_tag]:
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
                    '\n'.join([
                        six.text_type(n) for n, _ in parameters[name_tag]
                        ])
                    )
            if not [institution_obj] * len(parameters[name_tag]) == \
              [getattr(n, 'content_object')
               for n, _ in parameters[name_tag]]:
                raise Exception(
                    'The following institution names were found but they ' +
                    'are not associated with the same institution. ' +
                    'This must be fixed (e.g. by removing duplicate objects) ' +
                    'before we can proceed.\n' +
                    '\n'.join([
                        six.text_type(n) for n, _ in parameters[name_tag]
                        ])
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
        if self.edb_version.ge_version_2:
            instdetails_defaults.append('venue_info')
        instdetails_defaults = {
            x: parameters[x] for x in instdetails_defaults if x in parameters
        }
        instdetails_obj, instdetails_created = \
            InstitutionDetails.objects.update_or_create(
                defaults=instdetails_defaults,
                institution=institution_obj
            )
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

        for idx, coord in enumerate(parameters.get('coordinates', [])):
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

        with disable_signals(
                (post_save,
                 (DUID_RECACHE_OURPOINTS, DUID_SAVE_SERVICELOC_LATLON_CACHE))
        ):
            for idx, serviceloc_element in \
                enumerate(parameters.get('location', [])):
                parameters['location'][idx] = \
                    self.parse_and_create_serviceloc(institution_obj,
                                                     serviceloc_element)
        ourPoints(institution=institution_obj, cache_flush=True)

        return institution_obj

    def parse_uuid_node(self, node, **kwargs):
        uuid_text = self.parse_text_node(node, **kwargs)
        try:
            return uuid.UUID(hex=uuid_text)
        except ValueError:
            if not self.derive_uuids:
                raise
            if not uuid_text:
                raise ValueError("Can not derive UUID from empty string")
            uuid_derived = hashlib.md5(uuid_text).hexdigest()
            self.stdout.write_maybe('Transforming %s: Derive UUID with MD5: '
                                    '%s -> %s' % (
                                        node.tag,
                                        uuid_text,
                                        uuid_derived
                                    ))
            return uuid.UUID(hex=uuid_derived)

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
