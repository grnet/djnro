# Required Packages

## Dependencies

DjNRO heavily depends on the following:

* Python (<3 & >=2.6)
* memcached
* A mail server - Tested with exim
* python-dev
* libxml2-dev
* libxslt1-dev
* lib32z1-dev (System architecture independent)
* python packages located in requirements.txt, you can install them with `pip install -r requirements.txt`.

## Conditional Dependencies
* python-pip
* python-mysqldb (If you wish to use MySQL as the DB backend)
* mysql-client
* apache2 (We suggest apache with mod_rewrite enabled - use your preferred server in case you dont want to use shibboleth)
* gettext: only if one will be editing and compiling translations
* python-django-auth-ldap: if ldap authentication backend will be used.
* sentry for error logging and aggregation through the use of raven library

## Django Social Auth
User authentication via social media is carried out by the [python-social-auth](http://http://django-social-auth.readthedocs.org/en/latest/index.html) package.


## Pip requirements.txt file
DjNRO has also a requirements file which can be used with pip.

In addition to the core requirements in ````requirements.txt````, there are
also optional packages, needed for additional functinonality like rendering
data export templates (invoked separately outside of the Django application).
These are listed in ````requirements-optional.txt````.
