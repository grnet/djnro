import requests
from lxml import objectify


class CatQuery(object):

    def __init__(self, cat_key, cat_url):
        self.key = cat_key
        self.url = cat_url
        self.status = None
        self.response = None

    def post_request(self, kwargs):
        kwargs['APIKEY'] = self.key
        r = requests.post(self.url, data=kwargs)
        return r.content

    def curate_response(self, response):
        response = response.split('<CAT-API-Response>')[1]
        response = "<?xml version='1.0' ?><CAT-API-Response>"+response
        return response

    def newinst(self, kwargs):
        self.status = None
        self.response = None
        kwargs['ACTION'] = 'NEWINST'
        if 'NEWINST_PRIMARYADMIN' not in kwargs.keys():
            raise Exception('NEWINST_PRIMARYADMIN parameter is missing')
        response = self.post_request(kwargs)
        r = objectify.fromstring(response)
        try:
            assert(r.success)
            # Successfull response
            self.status = 'Success'
            self.response = {
                "inst_unique_id": r.success.inst_unique_id,
                "enrollment_URL": r.success.enrollment_URL
            }
            return True
        except AttributeError:
            self.status = 'Error'
            self.response = r.error.description
            return False

    def admincount(self, kwargs):
        self.status = None
        self.response = None
        kwargs['ACTION'] = 'ADMINCOUNT'
        if not 'INST_IDENTIFIER' in kwargs.keys():
            raise Exception('INST_IDENTIFIER parameter is missing')
        response = self.post_request(kwargs)
        response = self.curate_response(response)
        r = objectify.fromstring(response)
        try:
            assert(r.success)
            # Successfull response
            self.status = 'Success'
            self.response = {"number_of_admins":r.success.number_of_admins}
            return True
        except AttributeError:
            self.status = 'Error'
            self.response = r.error.description
            return False

    def statistics(self):
        self.status = None
        self.response = None
        kwargs = {}
        kwargs['ACTION'] = 'STATISTICS'
        response = self.post_request(kwargs)
        response = self.curate_response(response)
        r = objectify.fromstring(response)
        return r





