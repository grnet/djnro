from django.conf import settings
from django.template.defaulttags import register


@register.filter
def login_method_name(backend):
    for method in settings.MANAGE_LOGIN_METHODS:
        if method['backend'] == backend:
            return method['name']
    return backend
