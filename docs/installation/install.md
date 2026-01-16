# Installation & Configuration
First of all you have to install all the packages described in `requirements`
section

The project is published on [GitHub](https://github.com/grnet/djnro) and can be fetched using git:

	git clone https://github.com/grnet/djnro


## Project & Local Settings

**In version 0.9 settings were split in two parts: settings.py and local_settings.py**

The file `settings.py` contains settings distributed by the project, which should normally not be necessary to modify.
Options specific to the particular installation must be configured in `local_settings.py`. This file must be created by copying `local_settings.py.dist`:

    cd djnro
    cp djnro/local_settings.py.dist djnro/local_settings.py


The following variables/settings need to be altered or set:

Set Admin contacts:

	ADMINS = (
	     ('Admin', 'admin@example.com'),
	)

Set the database connection params:

	DATABASES = {
	    ...
	}

For a production instance and once DEBUG is set to False set the ALLOWED_HOSTS:

    ALLOWED_HOSTS = ['.example.com']
    SECRET_KEY = '<put some random long string here, eg. %$#%@#$^2312351345#$%3452345@#$%@#$234#@$hhzdavfsdcFDGVFSDGhn>'

Django social auth needs changes in the Extra Authentication Backends depending on which social auth you want to enable:

	EXTRA_AUTHENTICATION_BACKENDS = (
	    'djnro.djangobackends.shibauthBackend.shibauthBackend',
		...
		'django.contrib.auth.backends.ModelBackend',
	)

**The default Authentication Backends are in settings.py**

Since the front-end application includes a "nearest eduroam" function, global eduroam service locations are pulled from the KML file published on eduroam.org:

	EDUROAM_KML_URL = 'http://monitor.eduroam.org/kml/all.kml'

Depending on your AAI policy set an appropriate eduPerson entitlement:

	SHIB_AUTH_ENTITLEMENT = 'urn:mace:example.com:pki:user'

Mail server parameters:

	SERVER_EMAIL = "Example domain eduroam Service <noreply@example.com>"
	EMAIL_SUBJECT_PREFIX = "[eduroam] "

NRO recipients for notifications:

	NOTIFY_ADMIN_MAILS = ["mail1@example.com", "mail2@example.com"]

Set your cache backend (if you want to use one). For production instances you can go with memcached. For development you can keep the provided dummy instance:

- Memcached must be configured so it can store the complete kml file (1.5Mb~ currently).
- Reddis requires the extra dependencies ```redis``` and ```hiredis```.

MemCached:

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

Redis:

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379',
        }
    }

NRO specific parameters. These affect HTML templates:

	# Variable used to determine the active Realm object (in views and context processor)
	NRO_COUNTRY_CODE = 'tld'
	# main domain url used in right top icon, eg. http://www.grnet.gr
	NRO_DOMAIN_MAIN_URL = "http://www.example.com"
	# NRO federation name
	NRO_FEDERATION_NAME = "GRNET AAI federation"
	# "provided by" info for footer
	NRO_PROV_BY_DICT = {"name": "EXAMPLE NRO TEAM", "url": "http://noc.example.com"}
	# social media contact (Use: // to preserve https)
	NRO_PROV_SOCIAL_MEDIA_CONTACT = [
	                                {"url":"//soc.media.url", "icon":"icon.png", "name":"NAME1(eg. Facebook)"},
	                                {"url":"//soc.media.url", "icon":"icon.png",  "name":"NAME2(eg. Twitter)"},
	                                ]
	# map center (lat, lng)
	MAP_CENTER = (36.97, 23.71)
	# Helpdesk, used in base.html:
	NRO_DOMAIN_HELPDESK_DICT = {"name": _("Domain Helpdesk"), 'email':'helpdesk@example.com', 'phone': '12324567890', 'uri': 'helpdesk.example.com'}

Set the Realm country for REALM model:

	#Countries for Realm model:
	REALM_COUNTRIES = (
	             ('country_2letters', 'Country' ),
	            )

Please note that `REALM_COUNTRIES` must contain an entry where the country code matches the value set in `NRO_COUNTRY_CODE`.  (And, `NRO_COUNTRY_CODE` must also match the `country` value in the `Realm` object created later).

Optionally, configure also the login methods that should be available for institutional administrators to log in.

These are configured in the `MANAGE_LOGIN_METHODS` tuple - which contains a dictionary for each login method.  The default value in `local_settings.py.dist` comes prepopulated with a list of popular social login providers supported by `python-social-auth`, plus the `shibboleth` and `locallogin` backends.  For each login method, the following fields are available:
* `backend`: the name of the backend in python-social-auth (or the special value of `shibboleth` or `locallogin`)
* `enabled`: whether this login method is enabled
* `class`: Backend class to load.  Gets added to `settings.AUTHENTICATION_BACKENDS` automatically for enabled login methods.
* `name`: Human readable name of the authentiation method to present to users
* `local_image`: Relative path of a local static image to use as logo for the login method.
* `image_url`: Full URL of an image to use as logo for the login method.
* `fa_style`: Font-Awesome style to use as logo for the login method.

### Custom content in footer

If you need to present custom content in the footer at the bottom of the every page, you can add HTML/template code in `djnro/templates/partial/extra.footer.html`.


Attribute map to match your AAI policy and SSO software (typically Shibboleth SP):

	# Shibboleth attribute map
	SHIB_USERNAME = ['HTTP_EPPN']
	SHIB_MAIL = ['mail', 'HTTP_MAIL', 'HTTP_SHIB_INETORGPERSON_MAIL']
	SHIB_FIRSTNAME = ['HTTP_SHIB_INETORGPERSON_GIVENNAME']
	SHIB_LASTNAME = ['HTTP_SHIB_PERSON_SURNAME']
	SHIB_ENTITLEMENT = ['HTTP_SHIB_EP_ENTITLEMENT']

Django Social Auth parameters:

	SOCIAL_AUTH_TWITTER_KEY = ''
	SOCIAL_AUTH_TWITTER_SECRET = ''
	SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
	SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ' '
	SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = []


### eduroam CAT integration

DjNRO provides integration with eduroam CAT (Configuration Assistant Tool):

* Institution administrators can automatically provision their institution to CAT without the intervention of the federation (NRO) administrator.
* End users can search for their institution at the _connect_ page and get direct access to the tools (profiles and installers) provisioned in eduroam CAT.

In order to enable this functionality, you must list at least one instance and the corresponding description under the `CAT_INSTANCES` setting. Pages accessible by end users currently only show CAT data for the instance named `production`.

You must also set the following parameters for each CAT instance in `CAT_AUTH`:

* `CAT_API_KEY`: Admin API key for authentication to CAT
* `CAT_API_URL`: Admin API endpoint URL
* `CAT_USER_API_URL`: User API endpoint URL
* `CAT_USER_API_VERSION`: User API version
* `CAT_USER_API_LOCAL_DOWNLOADS`: Base URL for local app downloads (e.g. Android); derived from `CAT_USER_API_URL` if not configured
* `CAT_PROFILES_URL`: Base URL for the intitution download area pages
* `CAT_IDPMGMT_URL`: URL for the IdP overview page

```
CAT_INSTANCES = (
    ('production', 'cat.eduroam.org'),
    ('testing', 'cat-test.eduroam.org'),
)

CAT_AUTH = {
    'production': {
        "CAT_API_KEY": "<provided API key>",
        "CAT_API_URL": "https://cat.eduroam.org/admin/API.php",
        "CAT_USER_API_URL": "https://cat.eduroam.org/user/API.php",
        "CAT_USER_API_VERSION": 2,
        "CAT_USER_API_LOCAL_DOWNLOADS": "https://cat.eduroam.org/",
        "CAT_PROFILES_URL": "https://cat.eduroam.org/",
        "CAT_IDPMGMT_URL": "https://cat.eduroam.org/admin/overview_idp.php"
    },
    'testing': {
        "CAT_API_KEY": "<provided API key>",
        "CAT_API_URL": "https://cat-test.eduroam.org/test/admin/API.php",
        "CAT_USER_API_URL": "https://cat-test.eduroam.org/test/user/API.php",
        "CAT_USER_API_VERSION": 2,
        "CAT_USER_API_LOCAL_DOWNLOADS": "https://cat-test.eduroam.org/test/",
        "CAT_PROFILES_URL": "https://cat-test.eduroam.org/test",
        "CAT_IDPMGMT_URL": "https://cat-test.eduroam.org/test/admin/overview_idp.php"
    },
}
```

For more information about eduroam CAT, you may read [the guide to eduroam CAT for federation administrators](//wiki.geant.org/display/H2eduroam/A+guide+to+eduroam+CAT+2.0+and+eduroam+Managed+IdP+for+National+Roaming+Operator+administrators).

Please note: The front-end integration requires that DjNRO has a record of the institution CAT ID. If an institution is manually invited to eduroam CAT, rather than enrolling automatically through DjNRO, then the federation administrator should fill in the ID assigned to the institution in CAT, for example using the Django admin interface.

#### CAT User API proxy

CAT front-end integration with DjNRO works through the CAT User API proxy, which

* provides cross-origin access to the CAT instance User API endpoint URL,
* normalizes responses, if necessary and
* caches responses using a Django cache backend.

Fine-grained control is provided over cache lifetime, per CAT instance and User API method. The cache backend and key prefix can also be configured.

The proxy will redirect (rather than proxy) download requests to the backend CAT User API endpoint, for security, statistics and performance considerations; this can be changed.

It is also possible to enable the proxy to serve [CORS](//en.wikipedia.org/wiki/Cross-origin_resource_sharing) headers, so as to permit cross-origin requests, for example to accommodate embedding a CAT front-end in a different site and pointing it to the User API proxy.

The User API proxy is configured through settings `CAT_USER_API_CACHE_TIMEOUT` and `CAT_USER_API_PROXY_OPTIONS`. See the preceding comments in `local_settings.py.dist` for more details on all the above.

### Connect page customization for different eduroam CAT instances

The _connect_ page integrates a CAT user interface. All information provided therein is fetched from eduroam CAT, yet there are some static elements and text defined in the template, which include references specific to [cat.eduroam.org](//cat.eduroam.org/). Such parts are wrapped in template blocks whose names are prefixed with `cat_`. It is possible to extend this template and override such blocks, so as to customize the references for a different CAT instance:

```
{% extends "base.html" %}

{% block cat_redirect_msg %}
The message shown for CAT profiles/devices configured to redirect to a local page.
It should include an <a data-catui="device-redirecturl"> element.
{% endblock %}
{% block cat_signed_by %}
The tooltip message shown for digitally signed CAT downloads.
{% endblock %}
{% block cat_default_msg %}
The default user message shown when no EAP or device custom text is configured.
{% endblock %}
{% block cat_postinstall_msg %}
The message shown after device info.
{% endblock %}
{% block cat_support_header %}
The text shown before support contacts defined in CAT.
{% endblock %}
{% block cat_nosupport_header %}
The text shown when no support contacts are defined in CAT.
{% endblock %}
{% block cat_mailing_list %}
The note about the cat-users mailing list, shown after support contacts.
{% endblock %}
{% block cat_attribution %}
The footnote attributing the CAT service being used.
It should include an <a data-catui="cat-api-tou"> element.
{% endblock %}
{% block cat_institution_selector %}
The button acting as the institution selector for each individual institution in the institution list.
{% endblock %}
```

The custom template should then be configured in the `CAT_CONNECT_TEMPLATE` setting, for the `production` instance. See the default template in `djnro/templates/front/connect.html` and the preceding comments in `local_settings.py.dist` for more details.

Please note: In the default template, these blocks contain text marked for translation. While it is possible to follow suit in the customized template/blocks, it is not practical, since such custom text would have to be committed to the source file (`locale/en/LC_MESSAGES/django.po`). Unfortunately there is presently no solution for translating customized templates, other than overriding DjNRO-shipped PO/MO files and managing them on your own.

### Extra Apps
In case one wants to extend some of the default settings (configured in `settings.py`), one can prepend *EXTRA_* on the attribute to be amended. For example:

	EXTRA_INSTALLED_APPS = (
		'django_debug_toolbar',
	)

### Sentry integration
If you want to use [Sentry](https://sentry.io/for/django/) for error
logging (replacing e-mails sent by Django to SITE_ADMINS for
backtraces), complete the following steps:

1. Set up your [Sentry instance](https://docs.sentry.io/)
2. Install raven library, which is included in `requirements-optional.txt`
3. Update your `local_settings.py` so that it contains a `SENTRY`
    dictionary as in `local_settings.py.dist`
4. Update the parameters in the `SENTRY` as applicable to your setup:
    - Set `activate` to `True`.
    - Add your DSN in `sentry_dsn`; you can also use a `SENTRY_DSN`
      environment variable, but extra work would be necessary to have
      it exposed by Apache to `mod_wsgi` and Django. If you use both
      DSN options, the environment variable should prevail.

## Database Sync
Once you are done with `local_settings.py` run:

	./manage.py migrate

Create a supe-ruser, it comes in handy for access to Django admin.

	./manage.py createsuperuser

Now you should have a clean database with all the tables created (and a
single super-user).

## Setting up the canonical hostname

You must configure the canonical public hostname of your site for the
Django Sites Framework to work properly. This is used for example when
a stable, fully qualified URL must be produced (irrespective of the
HTTP host). You can use the Django admin interface (see the section
about *Initial Data*) and browse to
`https://<hostname>/admin/sites/site/1/` to modify the domain name for
the default object that was created upon installation, or you can
create another object and update `SITE_ID` in settings.

## Collecting static files

**Starting with version 1.1.1 the following process for provisioning
  static files is introduced in order to align with the
  Django-recommended practice and remove unrelated files from DjNRO.**

You need to run the following command in order to *collect* static
files from DjNRO and all other sources to the folder the HTTP server (such
as Apache) will serve them from.

This folder by default is `static` but this can be changed by setting
`STATIC_ROOT` in `local_settings.py`. This folder is expected to be
served under `/static` by default, but this can also be configured by
setting `STATIC_URL` in `local_settings.py`. If the defaults are
overridden, the HTTP server configuration should be updated accordingly.

	./manage.py collectstatic

Please note the directory `static` must be created manually before
running this command.

**If you are upgrading from a version prior to 1.1.1, make sure you
  backup any files you may have manually dropped into `static` before
  you run this command! If you want such files to be preserved and
  deployed by `collectstatic`, you can move them to `djnro/static`.**

This step will have to be repeated whenever an existing installation
is updated; at such time you should run the command with the
`--clear` parameter, but you should be careful not to remove any file
you manually copied to the `static` folder. Please run the command
with `--help` to see an explanation of all available options.

## Running the server
We suggest using Apache and mod_wsgi. Below is an example configuration:

	# Tune wsgi daemon as necessary: processes=x threads=y
	WSGIDaemonProcess djnro display-name=%{GROUP} python-path=/path/to/djnro/
	# If running in a virtualenv e.g. with python 2.7, append to python-path:
	# :<virtualenv-path>/lib/python2.7/site-packages

	<VirtualHost *:443>
		ServerName		example.com

		Alias		/static	/path/to/djnro/static
		WSGIScriptAlias	/	/path/to/djnro/djnro/wsgi.py
		<Directory /path/to/djnro/djnro>
			<Files wsgi.py>
			    WSGIProcessGroup djnro
			    Order deny,allow
			    Allow from all
			</Files>
		</Directory>

		SSLEngine on
		SSLCertificateFile	...
		SSLCertificateChainFile	...
		SSLCertificateKeyFile	...

		# Shibboleth SP configuration
		ShibConfig	/etc/shibboleth/shibboleth2.xml
		Alias		/shibboleth-sp	/usr/share/shibboleth

		# SSO through Shibboleth SP:
		<Location /login>
			AuthType shibboleth
			ShibRequireSession On
			ShibUseHeaders On
			require valid-user
		</Location>
		<Location /Shibboleth.sso>
			SetHandler shib
		</Location>
	</VirtualHost>

Alternatively, it is possible to use Apache with mod_proxy_http to pass the requests to uwsgi.  In that case, the ````WSGIScriptAlias```` directive would be replaced with the following:

                ProxyRequests off
                ProxyPreserveHost on

                ProxyPass / http://localhost:3031/
                ProxyPassReverse / http://localhost:3031/

                # tell DjNRO we have forwarded over SSL
                RequestHeader set X-Forwarded-Protocol https

**It is strongly recommended to allow access to `/(admin|overview|alt-login)` ONLY from trusted subnets.**

Once you are done, restart apache.

## Fetch KML
A Django management command, named fetch_kml, fetches service locations from the eduroam database and updates the cache. It is recommended to periodically run this command in a cron job in order to keep the map up to date.

	./manage.py fetch_kml 

*Tip: Run `manage.py` with `--verbosity=0` to disable informational output that may trigger unnecessary mail from a cron job.*

## Initial Data

In order to start using DjNRO you need to create a Realm record for your NRO along with one or more contacts linked to it. You can visit the Django admin interface `https://<hostname>/admin` and add a Realm (remember to set REALM_COUNTRIES in local_settings.py).
In DjNRO the NRO sets the environment for the institution eduroam admins. Therefore the NRO has to insert the initial data for his/her clients/institutions in the *Institutions* Model (table), again using the Django admin interface. As an alternative, you can parse your existing `institution.xml` and import institution data by running the following command:

	./manage.py parse_institution_xml /path/to/institution.xml

## Exporting Data
DjNRO can export data in formats suitable for use by other software.

XML documents conforming to the [eduroam database](//monitor.eduroam.org/fact_eduroam_db.php) schemata are exported at the following URLs, as required for harvesting by eduroam.org:

	/general/realm.xml
	/general/institution.xml
	/usage/realm_data.xml

A list of institution administrators can be exported in CSV format or a plain format suitable for use by a mailing list (namely [Sympa](http://www.sympa.org/manual/parameters-data-sources#include_remote_file). This data is available through:

* a management comand `./manage.py contacts`, which defaults to CSV output (*currently with headers in Greek!*) and can switch to plain output using `--mail-list`

* a view (`adminlist`), which only supports output in the latter plain text format

Likewise, data that can be used as input for automatic configuration of `Federation Level RADIUS Servers (FLRS)` can be exported in YAML/JSON format, through:

* a management command (`./manage.py servdata`)

* a view (`sevdata`)

Output format defaults to YAML and can be overriden respectively:

* by using `--output=json`

* by sending an `Accept: application/json` HTTP header

We also provide a sample script for reading this data (`extras/servdata_consumer.py`) along with templates (in the same directory) for producing configuration suitable for FreeRADIUS and radsecproxy. This script requires the following python packages:

  * python-requests

  * python-yaml

  * python-mako (for the templates)

Take the time to read the default settings at the top of the script and run it with `--help`. The templates are based on assumptions that may not match your setup; they are mostly provided as a proof of concept.

**The `adminlist` and `servdata` views are commented out by default in `djnro/urls.py`. Make sure you protect them (TLS, ACL and/or authentication) at the HTTP server before you enable them, as they may expose private/sensitive data.**

## Next Steps (Branding)

The majority of branding is done via the NRO variables in local_settings.py. You might also want to change the logo of the application. Within the `static/img/eduroam_branding` folder you will find the XCF files logo_holder, logo_small.

## Upgrade Instructions

* Backup your `settings.py` and `local_settings` file and any local modifications.

* Update the code.

* Copy `djnro/local_settings.py.dist` to `djnro/local_settings.py` and modify it to match your previous configuration.

* edit the apache configuration in order to work with the new location of wsgi and set the python-path attribute.

* remove old wsgi file `/path/to/djnro/apache/django.wsgi` and parent directory

* remove django-extensions from `INSTALLED_APPS`

* Add timeout in cache configuration

* Make sure you have installed the following required packages (some of these introduced in 0.9):

  * python-oauth2

  * python-requests

  * python-lxml

  * python-yaml

* run `./manage.py migrate`

   **You had previously copied `urls.py.dist` to `urls.py`. This is no longer supported; we now use `djnro/urls.py`. URLs that provide sensitive data are disabled (commented out) by default. You may have to edit the file according to your needs.**

## LDAP Authentication

If you want to use LDAP authentication, local_settings.py must be amended:

	EXTRA_AUTHENTICATION_BACKENDS = (
		...,
		'django_auth_ldap.backend.LDAPBackend',
		...,
	)

	# LDAP CONFIG
	import ldap
	from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
	AUTH_LDAP_BIND_DN = ""
	AUTH_LDAP_BIND_PASSWORD = ""
	AUTH_LDAP_SERVER_URI = "ldap://foo.bar.org"
	AUTH_LDAP_START_TLS = True
	AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=People, dc=bar, dc=foo",
	ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
	AUTH_LDAP_USER_ATTR_MAP = {
	      "first_name":"givenName",
	      "last_name": "sn",
	      "email": "mail
	      }
	# Set up the basic group parameters.
	AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
		"ou=Groups,dc=foo,dc=bar,dc=org",ldap.SCOPE_SUBTREE, objectClass=groupOfNames"
	)
	AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
	AUTH_LDAP_USER_FLAGS_BY_GROUP = {
		"is_active": "cn=NOC, ou=Groups, dc=foo, dc=bar, dc=org",
		"is_staff": "cn=staff, ou=Groups, dc=foo, dc=bar, dc=org",
		"is_superuser": "cn=NOC, ou=Groups,dc=foo, dc=bar, dc=org"
	}

## Cache Configuration (DjNRO Version 1.3 and Later)

As of DjNRO version 1.3, the `MemcacheCache` cache backend was replaced with the `PyMemcacheCache` backend, due to updating from using Django 1.11 to Django 4.2. The change was introduced in Django 3.2.

This change has a side effect on the command `./manage.py fetch_kml` (see [Fetch KML](#Fetch-KML)) when using the `PymemcacheCache` backend. The default maximum item size (i.e. the maximum size of a single item that can be held in cache) configured by the memached daemon is 1 Megabyte by default, but the kml file cached by DjNRO can be greater than 1 Megabyte. This can cause the command to fail due to being unable to cache the entire file.

To fix this, edit the memcached configuration file (usually located at `/etc/memcached.conf` on Debian systems), and change or add the option that controls the maximum item size. If no such file exists, one can be created, which will overwrite memcached's default settings.
```
# Maximum item size. Default is 1m. Maximum is 128m.
-I 16m
```
This will allow DjNRO to cache files larger than one Megabyte.

## Account Registration Salt (DjNRO Version 1.3.1 and Later)

DjNRO version 1.3.1 updates the project from running on Django 4.2 to Django 5.2. This required updating the package `django-registration` from version 3.4 to version 5.2.1.

However, a consequence of this change is that the account registration and activation flow changed between package versions. To make DjNRO work with this change, a new setting has been added to `local_settings.py`. This setting is called `REGISTRATION_SALT`.

This setting is used during the creation of activation keys for new users. For more information about this setting, refer to [the django-registration documentarion](https://django-registration.readthedocs.io/en/stable/activation-workflow.html#security-considerations).

Changing this setting is not *strictly* necessary, as per the django-registration documentation. However, we **STRONGLY** recommend changing the default value of this setting.
