from django.conf import settings

def country_code(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
            'COUNTRY_NAME': settings.NRO_COUNTRY_NAME,
            'COUNTRY_CODE': settings.NRO_COUNTRY_CODE, 
            'DOMAIN_MAIN_URL': settings.NRO_DOMAIN_MAIN_URL, 
            'DOMAIN_HELPDESK_DICT': settings.NRO_DOMAIN_HELPDESK_DICT,
            'MAP_CENTER': settings.MAP_CENTER,
            'DEV_TEAM': settings.NRO_DEV_BY_DICT,
            'SOCIAL_MEDIA_LIST': settings.NRO_DEV_SOCIAL_MEDIA_CONTACT,
            }
