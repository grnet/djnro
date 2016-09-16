from django.conf import settings


def country_code(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'COUNTRY_CODE': settings.NRO_COUNTRY_CODE,
        'COUNTRY_NAME': dict(settings.REALM_COUNTRIES)[settings.NRO_COUNTRY_CODE],
        'DOMAIN_MAIN_URL': settings.NRO_DOMAIN_MAIN_URL,
        'FEDERATION_NAME': settings.NRO_FEDERATION_NAME,
        'BRANDING': {
            'helpdesk': settings.NRO_DOMAIN_HELPDESK_DICT,
            'social_media': settings.NRO_PROV_SOCIAL_MEDIA_CONTACT,
            'service_provider': settings.NRO_PROV_BY_DICT,
        },
        'MAP_CENTER': settings.MAP_CENTER,
        'VERSION': settings.SW_VERSION,
        'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY if hasattr(settings,"GOOGLE_MAPS_API_KEY") else None,
    }


def cat_instances(context):
    return {'CAT_INSTANCES': settings.CAT_INSTANCES}

def manage_login_methods(context):
    return {'MANAGE_LOGIN_METHODS': settings.MANAGE_LOGIN_METHODS}
