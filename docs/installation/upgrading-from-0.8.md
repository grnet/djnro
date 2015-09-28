# Upgrading DjNRO from 0.8 to 1.0 or later

DjNRO 0.8 was developed with django 1.2. Version 1.0 was developed with django 1.4.2.

Dumpdata with the help of south (always keep a backup):
	./manage.py dumpdata --indent=4 --natural --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_0.8.json

## Install DjNro
Install DjNRO >= v1.0 by following the instructions.


## Patch widgets.py
Patch widgets.py (there is a bug in tinymce)
	--- widgets.py
	+++ widgets.py
	@@ -11,7 +11,7 @@
	 from django.contrib.admin import widgets as admin_widgets
	 from django.core.urlresolvers import reverse
	 from django.forms.widgets import flatatt
	-from django.forms.util import smart_unicode
	+from django.utils.encoding import smart_unicode
	 from django.utils.html import escape
	 from django.utils import simplejson
	 from django.utils.datastructures import SortedDict


## Migrate
We have to introduce south the the models of social auth:

	./manage.py migrate default 0001_initial --fake

And then run the real migration:

	./manage.py migrate


# Loading old data to a new instance
In case you want to load data to a new database one has to follow these extra
steps.
In the old installation of DjNRO:

 - install and add 'fixture_magic' to INSTALLED_APPS in settings.py
 - run:

 		./manage.py reorder_fixtures --settings='settings' /tmp/eduroam_0.8.json edumanage.name_i18n edumanage.url_i18n edumanage.contact edumanage.realm edumanage.realmdata edumanage.institution edumanage.institutiondetails edumanage.institutioncontactpool edumanage.serviceloc edumanage.instserver edumanage.instrealm edumanage.instrealmmon edumanage.monlocalauthnparam edumanage.monproxybackclient > /tmp/eduroam_0.8.ordered.json


Now in the new installation:

 - run `./manage.py loaddata --settings='settings' /tmp/eduroam_0.8.ordered.json`
 - Continue with the `Migrate` step from above.

