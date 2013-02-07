Copyright © 2011-2013 Greek Research and Technology Network (GRNET S.A.)

Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr) and
Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr), GRNET NOC

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND ISC DISCLAIMS ALL WARRANTIES WITH REGARD
TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL ISC BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
SOFTWARE.

=================
DjNRO
=================

DjNRO is more than keeping eduroam.org updated with data. In essence it is a distributed management application. 
It is distributed in the sense that information about each institution locations and services is kept up-to-date by each local eduroam administrator.
Keeping in pace with eduroam's federated nature, the implementation uses federated authentication/authorisation mechanisms, namely Shibboleth plus social media itegration. 
The local institution eduroam administrators can become DjNRO admins. Local eduroam administrators register to the application via Shibboleth. 
Once the accounts are acitvated, local eduroam admins can manage their eduroam locations, contact points and institution information. 
 

1. Tool requirements

* python-django
* python-django-extensions
* python-mysqldb
* mysql-client-5.1
* python-ipaddr
* python-django-south
* python-django-tinymce
* python-memcache
* python-django-registration
* apache2
* apache2-mod-rewrite
* apache2-shibboleth : The server should be setup as a Shibboleth SP
* A mail server - Tested with exim
* python-django-social-auth
 *  OpenId support depends on python-openid
 *  OAuth support depends on python-oauth2 

2. Installation

* Install all required packages/libs.
* settings.py changes:
 * Set database backend, static url, template dirs
 * Social Auth requires setting up the appropriate TEMPLATE_CONTEXT_PROCESSORS and AUTHENTICATION_BACKENDS
 * To use Shibboleth set a valid SHIB_AUTH_ENTITLEMENT
 * Set email settings SERVER_EMAIL, EMAIL_SUBJECT_PREFIX
 * To notify certain people uppon user registration set their email accounts at: NOTIFY_ADMIN_MAILS
 * Set TINYMCE_JS_URL
 * If you wish to use a cache backend (recomended) set the CACHE_BACKEND
 * NRO variables are used in templates:
  * NRO_COUNTRY_NAME, NRO_COUNTRY_CODE, NRO_DOMAIN_MAIN_URL, NRO_DEV_BY_DICT, NRO_DEV_SOCIAL_MEDIA_CONTACT, MAP_CENTER, NRO_DOMAIN_HELPDESK_DICT
 * If you wish to use LDAP for the overview set the LDAP_AUTH_SETTINGS
 * To use the django social auth plugin set the api keys/secret of the active social media auth providers
  * Django social auth is higly customizable: http://django-social-auth.readthedocs.org/en/latest/index.html

* Run:
 * ./manage.py syncdb (create a super-user)
 * ./manage.py migrate
* To start with, you must create a Realm with a related contact.
* It is suggested to do this via the admin interface.

Invite your users to use it.


