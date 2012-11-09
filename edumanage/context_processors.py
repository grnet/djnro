from django.conf import settings

def country_code(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'COUNTRY_CODE': settings.COUNTRY_CODE, 'DOMAIN_MAIN_URL': settings.DOMAIN_MAIN_URL, 'DOMAIN_HELPDESK_DICT': settings.DOMAIN_HELPDESK_DICT}