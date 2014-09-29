# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
# Django settings for djnro project.

# Copyright © 2011-2014 Greek Research and Technology Network (GRNET S.A.)
# Copyright © 2011-2014 Leonidas Poulopoulos (@leopoul)
# Copyright © 2011-2014 Zenon Mousmoulas

#Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr, @leopoul) and
#Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr), GRNET NOC
#

# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from django.utils.translation import ugettext as _
import os

here = lambda x: os.path.join(os.path.abspath(os.path.dirname(__file__)), x)
djnro_path = os.path.join(os.path.abspath(os.path.dirname(__file__)))
project_path = os.path.abspath(os.path.dirname(__name__))

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Athens'

LOCALE_PATHS = (
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locale'),
)

LANGUAGES = (
    ('el', _('Greek')),
    ('en', _('English')),
)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# STATIC_ROOT = os.path.join(project_path, 'static')
print os.path.join(project_path, 'static')
STATICFILES_DIRS = [
    os.path.join(project_path, 'static'),
]


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required so that RequestContext is passed into
    # template
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'edumanage.context_processors.country_code',
    'social_auth.context_processors.social_auth_by_type_backends',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'edumanage.middleware.WrongBackendExceptionMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'djangobackends.shibauthBackend.shibauthBackend',
    # 'django_auth_ldap.backend.LDAPBackend',
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.google.GoogleBackend',
    'social_auth.backends.contrib.linkedin.LinkedinBackend',
    'social_auth.backends.contrib.yahoo.YahooOAuthBackend',
    'social_auth.backends.yahoo.YahooBackend',
    'social_auth.backends.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'djnro.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'djnro.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(djnro_path, 'templates/'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'longerusername',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'django.contrib.markup',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'edumanage',
    'accounts',
    'south',
    'registration',
    'tinymce',
    'social_auth',
    'utils',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#         }
#     },
#     'handlers': {
#         'mail_admins': {
#             'level': 'ERROR',
#             'filters': ['require_debug_false'],
#             'class': 'django.utils.log.AdminEmailHandler'
#         }
#     },
#     'loggers': {
#         'django.request': {
#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': True,
#         },
#     }
# }


AUTH_PROFILE_MODULE = 'accounts.UserProfile'

LOGIN_URL = '/manage/login/'

KML_FILE = here('all.kml')
INST_XML_FILE = here('institution.xml')

EDUROAM_KML_URL = 'http://monitor.eduroam.org/kml/all.kml'



TINYMCE_JS_URL = '/static/js/tinymce/tiny_mce.js'

TINYMCE_DEFAULT_CONFIG = {
    'extended_valid_elements' :  'iframe[src|width|height|name|align]',
    'plugins': "table,spellchecker,paste,searchreplace",
    'theme': "advanced",
}


#Name_i18n, URL_i18n, language choice field
# If it's the same with LANGUAGES, simply do URL_NAME_LANGS = LANGUAGES
URL_NAME_LANGS = (
    ('en', 'English' ),
    ('el', 'Ελληνικά'),
)

SOCIAL_AUTH_FORCE_POST_DISCONNECT = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_CREATE_USERS = True
SOCIAL_AUTH_FORCE_RANDOM_USERNAME = False
SOCIAL_AUTH_SANITIZE_REDIRECTS = False
SOCIAL_AUTH_SLUGIFY_USERNAMES = True

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/manage/'
LOGIN_REDIRECT_URL = '/manage/'
SOCIAL_AUTH_INACTIVE_USER_URL = '/manage/'
SOCIAL_AUTH_FORCE_POST_DISCONNECT = True

FACEBOOK_EXTENDED_PERMISSIONS = ['email']


LINKEDIN_EXTRA_FIELD_SELECTORS = ['email-address', 'headline', 'industry']
LINKEDIN_SCOPE = ['r_basicprofile', 'r_emailaddress']

LINKEDIN_EXTRA_DATA = [('id', 'id'),
                       ('first-name', 'first_name'),
                       ('last-name', 'last_name'),
                       ('email-address', 'email_address'),
                       ('headline', 'headline'),
                       ('industry', 'industry')]


SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.user.get_username',
    'social_auth.backends.pipeline.user.create_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details',
)

import _version
SW_VERSION = _version.VERSION

def _dictmerge(a, b):
    """ deep merge two dictionaries """
    ret = dict(a.items() + b.items())
    for key in set(a.keys()) & set(b.keys()):
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            ret[key] = _dictmerge(a[key], b[key])
    return ret

from local_settings import *  # noqa
for var, val in [i for i in locals().items() if i[0].startswith('EXTRA_')]:
    name = var[len('EXTRA_'):]
    try:
        locals()[name] += val  # append list
    except TypeError:
        locals()[name] = _dictmerge(locals()[name], val)  # merge dict
