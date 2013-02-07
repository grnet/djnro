from django.core.urlresolvers import reverse
from django.conf import settings
from social_auth.exceptions import WrongBackend

class WrongBackendExceptionMiddleware(object):
    def process_exception(self, request, exception):
        # Get the exception info now, in case another exception is thrown later.
        if isinstance(exception, WrongBackend):
            return self.handle_404(request, exception)

    def handle_404(self, request, exception):
        if settings.DEBUG:
            from django.views import debug
            return debug.technical_404_response(request, exception)
        else:
            callback, param_dict = resolver(request).resolve404()
            return callback(request, **param_dict)

from django.core.urlresolvers import RegexURLResolver
def resolver(request):
    """
    Returns a RegexURLResolver for the request's urlconf.

    If the request does not have a urlconf object, then the default of
    settings.ROOT_URLCONF is used.
    """
    from django.conf import settings
    urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
    return RegexURLResolver(r'^/', urlconf)




