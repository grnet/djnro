# -*- coding: utf-8 -*- vim:fileencoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
# Django settings for djnro project.

# Copyright © 2011-2014 Greek Research and Technology Network (GRNET S.A.)
# Copyright © 2011-2014 Leonidas Poulopoulos (@leopoul)
# Copyright © 2011-2014 Zenon Mousmoulas
# Copyright © 2014      Stavros Kroustouris

# Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr),
# Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr) and Stavros Kroustouris
# (staurosk-at-noc-dot-grnet-dot-gr), GRNET NOC
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

from django.utils.translation import ugettext_lazy as _
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, 'djnro')

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LANGUAGES = (
    ('el', _('Greek')),
    ('en', _('English')),
    ('hu', _('Hungarian')),
)

# Use a custom user model (as replacement for longerusername)
AUTH_USER_MODEL = 'accounts.User'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# The canonical public hostname should be configured for the domain
# attribute of the site object that matches SITE_ID
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static'),
]


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#   'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates/'),
            os.path.join(BASE_DIR, 'templates/'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Required so that RequestContext is passed into
                # template
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'edumanage.context_processors.country_code',
                'edumanage.context_processors.cat_instances',
                'edumanage.context_processors.manage_login_methods',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django_dont_vary_on.middleware.RemoveUnneededVaryHeadersMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    # 'djangobackends.shibauthBackend.shibauthBackend',
    # 'django_auth_ldap.backend.LDAPBackend',
    # 'social.backends.twitter.TwitterOAuth',
    # 'social.backends.google.GoogleOpenIdConnect',
    # 'social.backends.facebook.FacebookOAuth2',

    # 'social.backends.google.GoogleOAuth2',
    # 'social.backends.google.GoogleOAuth',
    # 'social.backends.linkedin.LinkedinOAuth2',
    # 'social.backends.yahoo.YahooOpenId',
    # 'social.backends.open_id.OpenIdAuth',

    'django.contrib.auth.backends.ModelBackend',
)

# Include a minimal version (matching original hard-coded list in the welcome_manage.html template)
# Override this in local_settings.py
MANAGE_LOGIN_METHODS = (
  { 'backend': 'shibboleth', 'enabled': True, 'class': 'djangobackends.shibauthBackend.shibauthBackend', 'name': 'Shibboleth', 'local_image': 'img/image_shibboleth_logo_color.png' },
  { 'backend': 'google-oauth2', 'enabled': True, 'class': 'social_core.backends.google.GoogleOAuth2', 'name': 'Google', 'fa_style': 'fa fa-google fa-2x' },
  { 'backend': 'twitter', 'enabled': True, 'class': 'social_core.backends.twitter.TwitterOAuth', 'name': 'Twitter', 'fa_style': 'fa fa-twitter fa-2x' },
)
# Note: we are not explicitly adding backends from this list - they're already
# included in AUTHENTICATION_BACKENDS anyway.

ROOT_URLCONF = 'djnro.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'djnro.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'sortedm2m',
    'social_django',
    'edumanage',
    'accounts',
    'registration',
    'tinymce',
    'utils',
    'oauthlib',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

# DEFAULT_LOGGING copied over from django/utils/log.py:

# Mildly customized default logging for Django.
# This sends an email to the site admins on every HTTP 500 error - but skips
# for SuspiciousOperation of type DisallowedHost.
# Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded by mean of the NullHandler (DEBUG=False).
from utils.logging import skip_disallowed_host_suspicious_operations
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
	'skip_disallowed_host_suspicious_operations': {
	    '()': 'django.utils.log.CallbackFilter',
	    'callback': skip_disallowed_host_suspicious_operations,
	},
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false','skip_disallowed_host_suspicious_operations'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
    }
}


LOGIN_URL = '/manage/login/'

KML_FILE = os.path.join(PROJECT_DIR, 'all.kml')

EDUROAM_KML_URL = 'https://monitor.eduroam.org/kml/all.kml'

# Request session cookies to be marked as secure
SESSION_COOKIE_SECURE = True

TINYMCE_COMPRESSOR = True

TINYMCE_DEFAULT_CONFIG = {
    'extended_valid_elements' :  'iframe[src|width|height|name|align]',
    'plugins': "table,paste,searchreplace",
    'theme': "advanced",
    'entity_encoding': 'raw',
    'entities': '160,nbsp,173,shy,8194,ensp,8195,emsp,8201,thinsp,8204,zwnj,8205,zwj,8206,lrm,8207,rlm',
}


#Name_i18n, URL_i18n, language choice field
# If it's the same with LANGUAGES, simply do URL_NAME_LANGS = LANGUAGES
URL_NAME_LANGS = (
    ('en', 'English' ),
    ('el', 'Ελληνικά'),
    ('hu', 'Magyar'),
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


CAT_INSTANCES = ()

# How to convert ServiceLoc.wired to wired_no
# Default: Use a magic number for True, NULL for False
SERVICELOC_DERIVE_WIRED_NO = {
    True: 42,
    False: None,
}

SENTRY = dict()

import _version
SW_VERSION = _version.VERSION

def _dictmerge(a, b):
    """ deep merge two dictionaries """
    ret = dict(a.items() + b.items())
    for key in set(a.keys()) & set(b.keys()):
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            ret[key] = _dictmerge(a[key], b[key])
    return ret

from djnro.local_settings import *  # noqa
for var, val in [i for i in locals().items() if i[0].startswith('EXTRA_')]:
    name = var[len('EXTRA_'):]
    try:
        locals()[name] += val  # append list
    except TypeError:
        locals()[name] = _dictmerge(locals()[name], val)  # merge dict

if SENTRY.get('activate'):
    import raven
    sentry_dsn = os.getenv("SENTRY_DSN") or SENTRY['sentry_dsn']
    if not sentry_dsn:
        raise RuntimeError("Sentry dsn not configured neither as environmental"
                           " variable nor in the settings.py file")

    RAVEN_CONFIG = {
        'dsn': sentry_dsn,
        'release': raven.fetch_git_sha(BASE_DIR)
    }
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    LOGGING['handlers']['sentry'] = {
        'class': 'raven.contrib.django.handlers.SentryHandler'
    }
    LOGGING['loggers']['django.request']['handlers'] = ['sentry']
