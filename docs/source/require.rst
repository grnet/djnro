.. _require-label:

Required Packages
=================

Dependencies
^^^^^^^^^^^^
DjNRO heavily depends on the following:

* Python (<3 & >=2.6)
* memcached
* python-mysqldb (If you wish to use MySQL as the DB backend)
* mysql-client
* apache2 (We suggest apache with mod_rewrite enabled - use your preferred server)
* A mail server - Tested with exim
* python packages located in requirements.txt

Conditional Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^
* gettext: only if one will be editing and compiling translations
* python-django-auth-ldap: if ldap authentication backend will be used.

Django Social Auth
------------------
User authentication via social media is carried out by the `python-django-social-auth <http://http://django-social-auth.readthedocs.org/en/latest/index.html>`_ python-django-social-auth package. We have included python-django-social-auth 0.7.18 in repository because DjNRO requires WrongBackend from social_auth.exceptions; this does not exist in 0.7.0 which ships with Debian Wheezy.

Django Social Auth: Requirements - Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*  OpenId support depends on python-openid

*  OAuth support depends on python-oauth2

