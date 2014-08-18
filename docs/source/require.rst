.. _require-label:

Required Packages
=================

.. attention::
   Installation instructions assume a clean Debian Wheezy with Django 1.4

DjNRO heavily depends on the following:

* Python (<3 & >=2.6)
* Django (>=1.4) - python-django
* memcached
* python-mysqldb (If you wish to use MySQL as the DB backend)
* mysql-client-5.1
* python-ipaddr
* python-django-south (For database migrations). If you deploy MySQL >=5.5 and earlier versions of south (< 0.7.5), you are advised to upgrade to South >=0.7.5, as you may suffer from this `bug <http://south.aeracode.org/ticket/523>`_
* python-django-tinymce (Flatpages editing made easier)
* python-memcache (Yeap! You need that for Google maps locations caching)
* python-django-registration (User activation made easy)
* apache2 (We suggest apache with mod_rewrite enabled - use your preferred server)
* libapache2-mod-wsgi
* apache2-shibboleth : The server should be setup as a Shibboleth SP
* A mail server - Tested with exim
* python-oauth2
* python-requests
* python-lxml
* python-yaml
* gettext


Django Social Auth
------------------

User authentication via social media is carried out by the `django-social-auth <http://django-social-auth.readthedocs.org/en/latest/index.html>`_ django-social-auth package. If your distro includes it, then go via your distro installation.

In any case we have included django-social-auth as an application inside the djnro Django project. We plan to upgrade to python-social-auth in the next releases of DjNRO.

Django Social Auth: Requirements - Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* django-social-auth

 *  OpenId support depends on python-openid

 *  OAuth support depends on python-oauth2
