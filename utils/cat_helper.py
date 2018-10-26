import requests
from lxml import objectify
from lxml.etree import XMLSyntaxError
import re

# http://code.activestate.com/recipes/135435-sort-a-string-using-numeric-order/
def string_split_by_numbers(x):
    r = re.compile('(\d+)')
    l = r.split(x)
    return [int(y) if y.isdigit() else y for y in l]

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

    def newinst(self, kwargs):
        self.status = None
        self.response = None
        kwargs['ACTION'] = 'NEWINST'
        if 'NEWINST_PRIMARYADMIN' not in kwargs.keys():
            raise Exception('NEWINST_PRIMARYADMIN parameter is missing')
        response = self.post_request(kwargs)
        r = self.curate_response(response)
        try:
            assert r.success is not None
            # Successfull response
            self.status = 'Success'
            self.response = {
                "inst_unique_id": r.success.inst_unique_id,
                "enrollment_URL": r.success.enrollment_URL
            }
            return True
        except AttributeError:
            self.status = 'Error'
            try:
                self.response = r.error.description
            except AttributeError:
                pass
            return False

    def admincount(self, kwargs):
        self.status = None
        self.response = None
        kwargs['ACTION'] = 'ADMINCOUNT'
        if not 'INST_IDENTIFIER' in kwargs.keys():
            raise Exception('INST_IDENTIFIER parameter is missing')
        response = self.post_request(kwargs)
        r = self.curate_response(response)
        try:
            assert r.success is not None
            # Successfull response
            self.status = 'Success'
            self.response = {"number_of_admins":r.success.number_of_admins}
            return True
        except AttributeError:
            self.status = 'Error'
            try:
                self.response = r.error.description
            except AttributeError:
                pass
            return False

    def statistics(self):
        self.status = None
        self.response = None
        kwargs = {}
        kwargs['ACTION'] = 'STATISTICS'
        response = self.post_request(kwargs)
        r = self.curate_response(response)
        return r





