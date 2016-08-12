# Installation/Configuration
First of all you have to install all the packages described in `requirements`
section

The software is published at [github](https://github.com/grnet/djnro) and can be downloaded using git:

	git clone https://github.com/grnet/djnro


## Project & Local Settings

**In version 0.9 settings were split in two parts: settings.py and local_settings.py**

The file settings.py contains settings distributed by the project, which should normally not be necessary to modify.
Options specific to the particular installation must be configured in local_settings.py. This file must be created by copying local_settings.py.dist:

    cd djnro
    cp djnro/local_settings.py.dist djnro/local_settings.py


The following variables/settings need to be altered or set:

Set Admin contacts::

	ADMINS = (
	     ('Admin', 'admin@example.com'),
	)

Set the database connection params:

	DATABASES = {
	    ...
	}

For a production instance and once DEBUG is set to False set the ALLOWED_HOSTS:

    ALLOWED_HOSTS = ['.example.com']
    SECRET_KEY = '<put something really random here, eg. %$#%@#$^2312351345#$%3452345@#$%@#$234#@$hhzdavfsdcFDGVFSDGhn>'

Django social auth needs changes in the Extra Authentication Backends depending on which social auth you want to enable:

	EXTRA_AUTHENTICATION_BACKENDS = (
	    'djnro.djangobackends.shibauthBackend.shibauthBackend',
		...
		'django.contrib.auth.backends.ModelBackend',
	)

**The default Authentication Backends are in settings.py**

As the application includes a "Nearest eduroam" functionality, global eduroam service locations are harvested from the KML file published at eduroam.org::

	EDUROAM_KML_URL = 'http://monitor.eduroam.org/kml/all.kml'


Depending on your AAI policy set an appropriate authEntitlement::

	SHIB_AUTH_ENTITLEMENT = 'urn:mace:example.com:pki:user'

Mail server parameters::

	SERVER_EMAIL = "Example domain eduroam Service <noreply@example.com>"
	EMAIL_SUBJECT_PREFIX = "[eduroam] "

NRO contact mails::

	NOTIFY_ADMIN_MAILS = ["mail1@example.com", "mail2@example.com"]

Set your cache backend (if you want to use one). For production instances you can go with memcached. For development you can keep the provided dummy instance::


    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

NRO specific parameters. These affect HTML templates::

	# Variable used to determine the active Realm object (in views and context processor)
	NRO_COUNTRY_CODE = 'gr'
	# main domain url used in right top icon, eg. http://www.grnet.gr
	NRO_DOMAIN_MAIN_URL = "http://www.example.com"
	# NRO federation name
	NRO_FEDERATION_NAME = "GRNET AAI federation"
	# provider info for footer
	NRO_PROV_BY_DICT = {"name": "EXAMPLE DEV TEAM", "url": "http://devteam.example.com"}
	#NRO social media contact (Use: // to preserve https)
	NRO_PROV_SOCIAL_MEDIA_CONTACT = [
	                                {"url":"//soc.media.url", "icon":"icon.png", "name":"NAME1(eg. Facebook)"},
	                                {"url":"//soc.media.url", "icon":"icon.png",  "name":"NAME2(eg. Twitter)"},
	                                ]
	# map center (lat, lng)
	MAP_CENTER = (36.97, 23.71)
	#Helpdesk, used in base.html:
	NRO_DOMAIN_HELPDESK_DICT = {"name": _("Domain Helpdesk"), 'email':'helpdesk@example.com', 'phone': '12324567890', 'uri': 'helpdesk.example.com'}


Set the Realm country for REALM model::

	#Countries for Realm model:
	REALM_COUNTRIES = (
	             ('country_2letters', 'Country' ),
	            )

Please note that `REALM_COUNTRIES` must contain an entry where the country code matches the value set in `NRO_COUNTRY_CODE`.  (And, `NRO_COUNTRY_CODE` must also match the `country` value in the `Realm` object created later).

Optionally, configure also the login methods that should be available for institutional administrators to log in.

These are configured in the `MANAGE_LOGIN_METHODS` tuple - which contains a dictionary for each login method.  The default value `local_settings.py.dist` comes prepopulated with a list of popular social login providers supported by `python-social-auth`, plus the `shibboleth` and `locallogin` backends.  For each login method, the following fields are available:
* `backend`: the name of the backend in python-social-auth (or the special value of `shibboleth` or `locallogin`)
* `enabled`: whether this login method is enabled
* `class`: Backend class to load.  Gets added to `settings.AUTHENTICATION_BACKENDS` automatically for enabled login methods.
* `name`: Human readable name of the authentiation method to present to users
* `local_image`: Relative path of a local static image to use as logo for the login method.
* `image_url`: Full URL of an image to use as logo for the login method.
* `fa_style`: Font-Awesome style to use as logo for the login method.

### Custom content in footer

If you need to present custom content in the footer at the bottom of the every page, you can add HTML/template code in `djnro/templates/partial/extra.footer.html`.


Attribute map to match your AAI policy and SSO software (typically Shibboleth SP)::

	#Shibboleth attribute map
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


DjNRO provides limited integration with eduroam CAT (Configuration Assistant Tool). Institution administrators can automatically provision their institution to CAT without the intervention of the federation (NRO) administrator.

In order to enable this functionality, you must list at least one instance and the corresponding description in CAT_INSTANCES. Beware that pages accessible by end users currently only show CAT information
for the instance named `production`.

You must also set the following parameters for each CAT instance in CAT_AUTH:

* CAT_API_KEY: API key for authentication to CAT

* CAT_API_URL: API endpoint URL

* CAT_PROFILES_URL: Base URL for Intitution Download Area pages

* CAT_FEDMGMT_URL: URL For Federation Overview page (currently not in use)

::

    CAT_INSTANCES = (
        ('production', 'cat.eduroam.org'),
        ('testing', 'cat-test.eduroam.org'),
    )

    CAT_AUTH = {
        'production': {
            "CAT_API_KEY": "<provided API key>",
            "CAT_API_URL": "https://cat.eduroam.org/admin/API.php",
            "CAT_PROFILES_URL": "https://cat.eduroam.org/",
            "CAT_FEDMGMT_URL": "https://cat.eduroam.org/admin/overview_federation.php"
        },
        'testing': {
            "CAT_API_KEY": "<provided API key>",
            "CAT_API_URL": "https://cat-test.eduroam.org/test/admin/API.php",
            "CAT_PROFILES_URL": "https://cat-test.eduroam.org/test",
            "CAT_FEDMGMT_URL": "https://cat-test.eduroam.org/test/admin/overview_federation.php"
        },
    }

For more information about eduroam CAT, you may read: [A guide to eduroam CAT for federation administrators](https://confluence.terena.org/display/H2eduroam/A+guide+to+eduroam+CAT+for+federation+administrators).

### Extra Apps
In case one wants to extend some of the settings only for the local instance, they can prepend *EXTRA_* on the attribute they want to extend. For example:

	EXTRA_INSTALLED_APPS = (
		'django_debug_toolbar',
	)

## Database Sync
Once you are done with local_settings.py run:

	./manage.py syncdb

Create a superuser, it comes in handy. And then run south migration to complete::

	./manage.py migrate

Now you should have a clean database with all the tables created.

## Running the server


We suggest using Apache and mod_wsgi. Below is an example configuration::

	# Tune wsgi daemon as necessary: processes=x threads=y
	WSGIDaemonProcess djnro display-name=%{GROUP} python-path=/path/to/djnro/

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

*Info*: It is strongly recommended to allow access to `/(admin|overview|alt-login)` *ONLY* from trusted subnets.

Once you are done, restart apache.

## Fetch KML
A Django management command, named fetch_kml, fetches the KML document and updates the cache with eduroam service locations. It is suggested to periodically run this command in a cron job in order to keep the map up to date::

		./manage.py fetch_kml

## Initial Data

In order to start using DjNRO you need to create a Realm record for your NRO along with one or more contacts linked to it. You can visit the Django admin interface `https://<hostname>/admin` and add a Realm (remember to set REALM_COUNTRIES in local_settings.py).
In DjNRO the NRO sets the environment for the institution eduroam admins. Therefore the NRO has to insert the initial data for his/her clients/institutions in the *Institutions* Model, again using the Django admin interface. As an alternative, you can copy your existing `institution.xml` to `/path/to/djnro` and run the following to import institution data::

		./manage.py parse_institution_xml

## Exporting Data
DjNRO can export data in formats suitable for use by other software.

XML documents conforming to the [eduroam database](https://monitor.eduroam.org/database.php>) schemata are exported at the following URLs, as required for harvesting by eduroam.org:

    /general/realm.xml
    /general/institution.xml
    /usage/realm_data.xml

A list of institution administrators can be exported in CSV format or a plain format suitable for use by a mailing list (namely [Sympa](http://www.sympa.org/manual/parameters-data-sources#include_remote_file>). This data is available through:

* a management comand `./manage.py contacts`, which defaults to CSV output (currently with headers in Greek!) and can switch to plain output using `--mail-list`.

* a view (`adminlist`), which only supports output in the latter plain text format.

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

*attention*
   **The `adminlist` and `servdata` views are commented out by default in `djnro/urls.py`. Make sure you protect them (SSL, ACL and/or authentication) at the HTTP server before you enable them, as they may expose private/sensitive data.**

## Next Steps (Branding)

The majority of branding is done via the NRO variables in local_settings.py. You might also want to change the logo of the application. Within the static/img/eduroam_branding folder you will find the XCF files logo_holder, logo_small.

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

*attention*

   **You had previously copied `urls.py.dist` to `urls.py`. This is no longer supported; we now use `djnro/urls.py`. URLs that provide sensitive data are disabled (commented out) by default. You may have to edit the file according to your needs.**

## LDAP Authentication

If you want to use LDAP authentication, local_settings.py must be amended::

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


## Pebble Watch Application - pebduroam


The closest point API allows for development of location aware-applications.
Pebduroam is a Pebble watch application that fetches the closest eduroam access point plus walking instructions on how to reach it.
Installing the application on your Pebble watch can be done in 2 ways:

* You can install the application via the Pebble App Store: [pebduroam](https://apps.getpebble.com/applications/5384b2119c84af48350000c7>)

* You can install the application and contribute to its development via github: [pebduroam github repo](https://github.com/leopoul/pebduroam>).

  * You need to have a Cloudpebble account to accomplish this.

  * Once logged-in you need to select Import - Import from github and paste the pebduroam github repo url in the corresponding text box.

  * Having configured your Pebble watch in developer mode will allow you to build and install your cloned project source directly on your watch.

**attention**
   Currently pebduroam uses GRNET's djnro closest point API. To switch the Pebble app to your djnro installation you need to follow the second method of installation

