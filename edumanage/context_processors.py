from django.conf import settings


def country_code(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'COUNTRY_NAME': settings.NRO_COUNTRY_NAME,
        'COUNTRY_CODE': settings.NRO_COUNTRY_CODE,
        'DOMAIN_MAIN_URL': settings.NRO_DOMAIN_MAIN_URL,
        'DOMAIN_HELPDESK_DICT': settings.NRO_DOMAIN_HELPDESK_DICT,
        'MAP_CENTER': settings.MAP_CENTER,
        'PROV_TEAM': settings.NRO_PROV_BY_DICT,
        'SOCIAL_MEDIA_LIST': settings.NRO_PROV_SOCIAL_MEDIA_CONTACT,
        'VERSION': settings.SW_VERSION,
        'API_KEY': settings.GOOGLE_API_KEY
    }


def cat_instances(context):
    return {'CAT_INSTANCES': settings.CAT_INSTANCES}
