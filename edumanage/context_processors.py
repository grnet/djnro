from django.conf import settings


def country_code(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'COUNTRY_NAME': settings.NRO_COUNTRY_NAME,
        'COUNTRY_CODE': settings.NRO_COUNTRY_CODE,
        'DOMAIN_MAIN_URL': settings.NRO_DOMAIN_MAIN_URL,
        'BRANDING': {
            'helpdesk': settings.NRO_DOMAIN_HELPDESK_DICT,
            'social_media': settings.NRO_PROV_SOCIAL_MEDIA_CONTACT,
            'service_provider': settings.NRO_PROV_BY_DICT,
        },
        'MAP_CENTER': settings.MAP_CENTER,
        'VERSION': settings.SW_VERSION
    }


def cat_instances(context):
    return {'CAT_INSTANCES': settings.CAT_INSTANCES}
