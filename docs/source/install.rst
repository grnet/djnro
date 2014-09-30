.. _install-label:

Installation/Configuration
==========================
.. contents::

.. attention::
   Installation instructions assume a clean Debian Wheezy with Django 1.4

Assuming that you have installed all the requirements described in :ref:`require-label` you can install the DjNRO project.

The software is published at code.grnet.gr and can be downloaded using git::

	git clone https://code.grnet.gr/git/djnro
	
It is also available on GitHub::

	https://github.com/grnet/djnro/


Project & Local Settings
^^^^^^^^^^^^^^^^^^^^^^^^

.. attention::
   In version 0.9 settings were split in two parts: settings.py and local_settings.py

The file settings.py contains settings distributed by the project, which should normally not be necessary to modify. Options specific to the particular installation must be configured in local_settings.py. This file must be created by copying local_settings.py.dist::

    cd djnro
    cp djnro/local_settings.py.dist djnro/local_settings.py



The following variables/settings need to be altered or set:

Set Admin contacts::

	ADMINS = (
	     ('Admin', 'admin@example.com'),
	)

Set the database connection params::

	DATABASES = {
	    ...
	}

For a production instance and once DEBUG is set to False set the ALLOWED_HOSTS::

    ALLOWED_HOSTS = ['.example.com']

Set your timezone and Languages::

	TIME_ZONE = 'Europe/Athens'

	LANGUAGES = (
	    ('el', _('Greek')),
	    ('en', _('English')),
	)

Set your static root and url::

    STATIC_ROOT = '/path/to/static'
    STATIC_URL = 'http://www.example.com/static'

Set the secret key::

    SECRET_KEY = '<put something really random here, eg. %$#%@#$^2312351345#$%3452345@#$%@#$234#@$hhzdavfsdcFDGVFSDGhn>'

Django social auth needs changes in the Authentication Backends depending on which social auth you want to enable::

	AUTHENTICATION_BACKENDS = (
	    'djnro.djangobackends.shibauthBackend.shibauthBackend',
		...
		'django.contrib.auth.backends.ModelBackend',
	)

Set your template dirs::

	TEMPLATE_DIRS = (
	    "/example/templates",
	)

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

Models Name_i18n and URL_i18n include a language choice field
If languages are the same with LANGUAGES variable, simply do URL_NAME_LANGS = LANGUAGES else set your own::

	URL_NAME_LANGS = (
	        ('en', 'English' ),
	        ('el', 'Ελληνικά'),
	    )

NRO specific parameters. These affect HTML templates::

	# Frontend country specific vars, eg. Greece
	NRO_COUNTRY_NAME = _('My Country')
	# Variable used by context_processor to display the "eduroam | <country_code>" in base.html
	NRO_COUNTRY_CODE = 'gr'
	# main domain url used in right top icon, eg. http://www.grnet.gr
	NRO_DOMAIN_MAIN_URL = "http://www.example.com"
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

Attribute map to match your AAI policy and SSO software (typically Shibboleth SP)::

	#Shibboleth attribute map
	SHIB_USERNAME = ['HTTP_EPPN']
	SHIB_MAIL = ['mail', 'HTTP_MAIL', 'HTTP_SHIB_INETORGPERSON_MAIL']
	SHIB_FIRSTNAME = ['HTTP_SHIB_INETORGPERSON_GIVENNAME']
	SHIB_LASTNAME = ['HTTP_SHIB_PERSON_SURNAME']
	SHIB_ENTITLEMENT = ['HTTP_SHIB_EP_ENTITLEMENT']

Django Social Auth parameters::

	TWITTER_CONSUMER_KEY = ''
	TWITTER_CONSUMER_SECRET = ''

	FACEBOOK_APP_ID = ''
	FACEBOOK_API_SECRET = ''

	LINKEDIN_CONSUMER_KEY        = ''
	LINKEDIN_CONSUMER_SECRET     = ''

	YAHOO_CONSUMER_KEY = ''
	YAHOO_CONSUMER_SECRET = ''

	GOOGLE_SREG_EXTRA_DATA = []

.. versionadded:: 0.9

Support for eduroam CAT can be set via the corresponding variables/dicts. Make sure to **always** include a 'production' instance record for CAT_INSTANCES and CAT_AUTH.
What you really need to make CAT work is a CAT_API_KEY and the CAT_API_URL. The CAT_PROFILES_URL is the base url of the landing page where your institution users can download device profile configurations::

    CAT_INSTANCES = (
                     ('production', 'Production Instance'),
                     ('testing', 'Testing Instance'),
                     ('dev1', 'Dev1 Instance'),
                     )

    CAT_AUTH = {
                'production':{"CAT_API_KEY":"<provided API key>",
                              "CAT_API_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                              "CAT_PROFILES_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                              "CAT_FEDMGMT_URL":"https://cat.eduroam.org/admin/overview_federation.php"},
                'testing':{"CAT_API_KEY":"<provided API key>",
                            "CAT_API_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                            "CAT_PROFILES_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                            "CAT_FEDMGMT_URL":"https://cat.eduroam.org/admin/overview_federation.php"},
                'dev1':{"CAT_API_KEY":"<provided API key>",
                            "CAT_API_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                            "CAT_PROFILES_URL":"https://cat-test.eduroam.org/test/admin/API.php",
                            "CAT_FEDMGMT_URL":"https://cat.eduroam.org/admin/overview_federation.php"},
                }

For more info on eduroam CAT, you can visit: `A guide to eduroam CAT for federation administrators <https://confluence.terena.org/display/H2eduroam/A+guide+to+eduroam+CAT+for+federation+administrators>`_.

In case one wants to extend some of the settings only for the local instance, they can prepend 'EXTRA_' on the attribute they want to extend. For example::
 
	EXTRA_INSTALLED_APPS = (
		'django_debug_toolbar',
	)

Database Sync
^^^^^^^^^^^^^

Once you are done with local_settings.py run::

	./manage.py syncdb

Create a superuser, it comes in handy. And then run south migration to complete::

	./manage.py migrate

Now you should have a clean database with all the tables created.

Running the server
^^^^^^^^^^^^^^^^^^

We suggest going via Apache with mod_wsgi. Below is an example configuration::

	WSGIDaemonProcess	djnro		processes=3 threads=20 display-name=%{GROUP} python-path=/path/to/djnro/
	WSGIProcessGroup	djnro

	...

	<VirtualHost *:443>
		ServerName		example.com
		ServerAdmin		admin@example.com
		ServerSignature		On

		<Files wsgi.py>
		    Order deny,allow
		    Allow from all
	    </Files>


		SSLEngine on
		SSLCertificateFile	...
		SSLCertificateChainFile ...
		SSLCertificateKeyFile	...

		# Shibboleth SP configuration
		ShibConfig		/etc/shibboleth/shibboleth2.xml
		Alias			/shibboleth-sp	/usr/share/shibboleth

	    # Integration of Shibboleth into Django app:

		<Location /login>
			AuthType shibboleth
			ShibRequireSession On
			ShibUseHeaders On
			require valid-user
		</Location>


		<Location /Shibboleth.sso>
			SetHandler shib
		</Location>


		Alias /static 		/path/to/djnro/static
		WSGIScriptAlias /      /path/to/djnro/djnro/wsgi.py
		ErrorLog /var/log/apache2/error.log
        CustomLog /var/log/apache2/access.log combined
	</VirtualHost>

*Info*: It is strongly suggested to allow access to /admin|overview|alt-login *ONLY* from trusted subnets.

Once you are done, restart apache.

Fetch kml
^^^^^^^^^
A Django management command, named fetch_kml, fetches the KML document and updates the cache with eduroam service locations. It is suggested to periodically run this command in a cron job in order to keep the map up to date::

		./manage.py fetch_kml

Initial Data
^^^^^^^^^^^^
In order to start using DjNRO you need to create a Realm record for your NRO along with one or more contacts linked to it. You can visit the Django admin interface (https://<hostname>/admin) and add a Realm (remember to set REALM_COUNTRIES in local_settings.py).
In DjNRO the NRO sets the environment for the institution eduroam admins. Therefore the NRO has to insert the initial data for his/her clients/institutions in the *Institutions* Model, again using the Django admin interface.

Next Steps (Set your Logo)
^^^^^^^^^^^^^^^^^^^^^^^^^^
The majority of branding is done via the NRO variables in local_settings.py. You might also want to change the logo of the application. Within the static/img/eduroam_branding folder you will find the XCF files logo_holder, logo_small. Edit with Gimp according to your needs and export to logo_holder.png and logo_small.png at the same path. To change the domain logo on top right, replace the static/img/right_logo_small.png file with your own logo (86x40).

Upgrade Instructions
^^^^^^^^^^^^^^^^^^^^
* Backup your settings.py file and any local modifications.

* Update the code.

* Copy local_settings.py.dist to local_settings.py and modify it to match your previous configuration configuration.

* edit the apache configuration in order to work with the new location of wsgi and
set the python-path attribute.

* remove old wsgi file '/path/to/djnro/apache/django.wsgi'

* remove django-extensions from `INSTALLED_APPS`

* Add timeout in cache configuration

* Make sure you have installed the following required packages (some of these introduced in 0.9):

	* python-oauth2

	* python-requests

	* python-lxml

	* python-yaml

* run manage.py migrate


Pip Support
^^^^^^^^^^^^
We have added a requirements.txt file, tested for django 1.4.5. You can use it
with `pip install -r requirements.txt`.


LDAP Authentication
^^^^^^^^^^^^^^^^^^^
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

