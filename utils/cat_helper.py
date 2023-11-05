import requests
from lxml import objectify
from lxml.etree import XMLSyntaxError
import re

# http://code.activestate.com/recipes/135435-sort-a-string-using-numeric-order/
def string_split_by_numbers(x):
    r = re.compile('(\d+)')
    l = r.split(x)
    return [int(y) if y.isdigit() else y for y in l]

def safe_get(o, prop, default):
    if isinstance(o, objectify.ObjectifiedElement):
        return getattr(o, prop, default)
    try:
        return o.get(prop, default)
    except AttributeError:
        try:
            assert isinstance(o, (str, unicode)) != True
            return o[prop]
        except:
            return default

def deep_get(o, *props, **opts):
    default = opts.get('default')
    for prop in props:
        o = safe_get(o, prop, default)
        if o == default:
            break
    return o

class CatQuery(object):

    def __init__(self, cat_key, cat_url):
        self.key = cat_key
        self.url = cat_url
        self.status = None
        self.response = None

    def post_request(self, kwargs):
        kwargs['APIKEY'] = self.key
        data=[]
        files=[]
        # produce a seq. number sorted list of params for POST
        # order is important for profile-api:eaptype
        for k in sorted(kwargs, key=string_split_by_numbers):
            # 'value[Sxx-2]' datatype: "file"
            if (k.startswith('value[S') and k.endswith('-2]')):
                files.append((k, kwargs[k]))
            else:
                data.append((k, kwargs[k]))
        r = requests.post(self.url, data=data, files=files)
        return r.content

    @staticmethod
    def curate_response(response):
        try:
            o = objectify.fromstring(response)
            assert o.tag == 'CAT-API-Response'
            return o
        except (XMLSyntaxError, AssertionError):
            return objectify.Element('Dummy')

    """ Send a CATv2 API request """
    def v2api_request(self, verb, params):
        apiRequest = {
            "ACTION": verb,
            "APIKEY": self.key,
            "PARAMETERS": params
        }
        r = requests.post(self.url, json=apiRequest)
        try:
            return r.json()
        except ValueError:
            return r.content

    ''' This is necessary to avoid rewriting other parts of DjNRO. It
    effectively munges the CATv1 API's parameter format into CATv2 JSON.
    Ironically CATv2 currently does the inverse and this is a counterpart
    to the uglify() method at https://github.com/GEANT/CAT/blob/master/web/lib/admin/API.php
    '''
    def deuglify(self, kwargs):
        params = [None]*(len(kwargs)//2);
        for k in sorted(kwargs, key=string_split_by_numbers):
            m = re.search(r"\[S(\d+)", k);
            id = 0
            if m:
                id = int(m.group(1))
            if k.startswith('option[S'):
                params[id] = dict()
                params[id]['NAME'] = kwargs[k]
            elif k.startswith('value[S'):
                if k.endswith('-lang]'):
                    params[id]['LANG'] = kwargs[k]
                else:
                    params[id]['VALUE'] = kwargs[k]
        return list(filter(None, params))

    """ Add an administrator into an institution """
    def adminadd(self, kwargs):
        self.status = None
        self.response = None
        if 'NEWINST_PRIMARYADMIN' not in kwargs.keys():
            raise Exception('NEWINST_PRIMARYADMIN parameter is missing')
        response = self.v2api_request('ADMIN-ADD', [
            {
                'NAME': 'ATTRIB-ADMINID',
                'VALUE': kwargs['NEWINST_PRIMARYADMIN'],
            },
            {
                'NAME': 'ATTRIB-CAT-INSTID',
                'VALUE': kwargs['INST_IDENTIFIER'],
            },
            {
                'NAME': 'ATTRIB-TARGETMAIL',
                'VALUE': kwargs['NEWINST_PRIMARYADMIN'],
            },
        ])
        if deep_get(response, 'result') == 'SUCCESS':
            self.status = 'Success'
            self.response = {
                "inst_unique_id": kwargs['INST_IDENTIFIER'],
                "enrollment_URL": deep_get(response, 'details', 'TOKEN URL'),
                "enrollment_token": deep_get(response, 'details', 'TOKEN')
            }
            return True
        else:
            self.status = 'Error'
            self.response = deep_get(response, 'details', 'description')
            return False

    """ Create a new institution, optionally adding an administrator to emulate the v1 behaviour. """
    def newinst(self, kwargs):
        self.status = None
        self.response = None
        params = self.deuglify(kwargs);
        response = self.v2api_request('NEWINST', params)
        if deep_get(response, 'result') == 'SUCCESS':
            kwargs['INST_IDENTIFIER'] = deep_get(response, 'details', 'ATTRIB-CAT-INSTID')
            if 'NEWINST_PRIMARYADMIN' in kwargs.keys():
                return self.adminadd(kwargs)
            else:
                self.status = 'Success'
                self.response = {
                    "inst_unique_id": deep_get(response, 'details', 'ATTRIB-CAT-INSTID')
                }
                return True
        else:
            self.status = 'Error'
            self.response = deep_get(response, 'details', 'description')
            return False

    """ Emulate the v1 ADMINCOUNT function from ADMIN-LIST """
    def admincount(self, kwargs):
        self.status = None
        self.response = None
        if not 'INST_IDENTIFIER' in kwargs.keys():
            raise Exception('INST_IDENTIFIER parameter is missing')
        response = self.v2api_request('ADMIN-LIST', [ { 'NAME': 'ATTRIB-CAT-INSTID', 'VALUE': kwargs['INST_IDENTIFIER'] } ])
        if deep_get(response, 'result') == 'SUCCESS':
            self.status = 'Success'
            self.response = {"number_of_admins": len(deep_get(response, 'details', default=[]))}
            return True
        else:
            self.status = 'Error'
            self.response = deep_get(response, 'details', 'description')
            return False

    def statistics(self):
        self.status = None
        self.response = None
        response = self.v2api_request('STATISTICS-FED', None)
        return deep_get(response, 'details', default={})
