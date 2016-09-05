# Use case: migration from 0.8 to 1.0

GRNET had been running the production DjNRO v0.8 instance on Django 1.2 (on Debian Squeeze). The MySQL database had been created with MyISAM tables. GRNET wanted to migrate this installation (both the application and the database) to a different host (Debian Wheezy), upgrade to latest code and Django 1.4 and at the same time migrate the database to the InnoDB engine. Achieving this by means of dumping and restoring the database was deemed too complicated and risky, as the SQL dump would have to be edited in order to properly recreate the database with InnoDB. Therefore it was decided to use Django dumpdata/loaddata to transfer the data to the new installation. The following sections document the steps taken in this process (most actions performed on the new host).

### Installing required software

We wanted to install both the old (v0.8) and current versions of DjNRO on the new host. The old version would serve as a snapshot of the production instance, so as to test actions in preparation of the migration without touching production.

We also prefer installing Debian-provided python packages for essential software, so as to have security updates, whereas installation through PyPI would provide latest versions of the software, which are however not required in our installation, but would also require compilers and development tools that we would rather not install in this environment. Therefore, with regards to python requirements, the installation would use a mix of Debian packages and packages installed with `pip` in a virtual environment.

1. Install required software with Debian packages:
    - apache2-mpm-worker
    - memcached
    - mysql-server
    - libapache2-mod-wsgi
    - libapache2-mod-shib2 (for SAML federated login)
    - python (= python 2.7)
    - python-pip (this will also install python 2.6)
    - python-virtualenv (this also requires python-pip)
    - git

1. Install optional Debian packages:
    - mysql-client (for manage.py dbshell)
    - gettext (for translation development)
    - ipython (for a better python shell)
    - winpdb (for python debugging)
    - patch

1. Install Debian python packages (rather than using pip to install them as requirements in a virtualenv):
    - python-mysqldb
    - python-memcache
    - python-lxml
    - python-yaml

1. Likewise install these packages instead of *security* requirements for `python-requests` (which will be installed in a virtualenv):
    - python-openssl
    - python-ndg-httpsclient
    - python-pyasn1

1. Install these packages to fulfill some dependencies for Python Social Auth:
    - python-httplib2
    - python-oauth2
    - python-openid

1. Install Debian packages for Django and some addons:
    - python-django
    - python-django-auth-ldap (for LDAP authentication, this will also install `python-django`)

**Note:** Installing `python-django-auth-ldap` would also install Django 1.4 outside a virtual environment. That would not be a problem as we were still targetting to use Debian-provided Django 1.4. However one could also install the `python-ldap` Debian package and install `django-ldap` and `Django` inside the virtualenv. In any case we don't want to install `python-ldap` with pip for the reasons stated earlier.

### Creating virtual environments

For a number of reasons we want to use *relocatable* virtual environments, for example so that we could move a virtualenv to a different path and apps installed therein would still work after that.

We thus create a virtualenv like this:

    virtualenv --python=/usr/bin/python2.7 --system-site-packages /path/to/virtualenv

We then need to patch `/path/to/virtualenv/bin/activate` so that it will work with a *relocated* virtualenv:

```
patch -p1 /path/to/virtualenv/bin/activate <<'EOF'
--- a/activate        2015-09-28 03:12:24.000000000 +0300
+++ b/activate        2015-09-28 03:12:57.000000000 +0300
@@ -37,7 +37,16 @@
 # unset irrelavent variables
 deactivate nondestructive
 
-VIRTUAL_ENV="/path/to/virtualenv"
+if [ -n "$BASH" ]; then
+    VIRTUAL_ENV=$(readlink -f "${BASH_SOURCE}" | sed 's#/bin/activate[^/]*$##')
+elif [ -n "$ZSH_VERSION" ]; then
+    VIRTUAL_ENV=$(readlink -f "${(%):-%N}" | sed 's#/bin/activate[^/]*$##')
+else
+    return 1
+fi
+if [ -z "$VIRTUAL_ENV" ]; then
+    return 1
+fi
 export VIRTUAL_ENV
 
 _OLD_VIRTUAL_PATH="$PATH"
EOF
```

A similar treatment is needed for scripts targetting different shells (`/path/to/virtualenv/bin/activate.{csh,fish}`), otherwise the `VIRTUAL_ENV` variable set therein should be updated once the virtualenv is *relocated*.

We then make the virtualenv relocatable. This command should be executed whenever virtualenv-installed packages install files in `/path/to/virtualenv/bin`.

    virtualenv --relocatable /path/to/virtualenv

Using this process we shall create two virtual environments:

- one for running the old version of DjNRO on Django 1.2 and
- one for setting up the target version of DjNRO on Django 1.4

In each of these we shall install a number of packages using `pip`:

#### *Old* virtualenv

- `Django==1.2.3`
- `South==0.7.5` (the particular version is required due to [an issue affecting `edumanage/migrations/0028...`](https://lists.grnet.gr/wws/arc/djnro/2013-02/msg00001.html))
- `django-extensions==0.5`
- `django-registration==0.7`
- `django-tinymce==1.5` (**with patch**, see below)
- `django-fixture-magic==0.0.7` (we will need to reorder fixtures with forward references)
- `ipaddr==2.1.11`
- `oauth==1.0.1`

**Note:** There is a minor issue with django-tinymce 1.5 that must be fixed:

```
patch -p1 /path/to/virtualenv/lib/python2.7/site-packages/tinymce/widgets.py <<'EOF'
--- a/widgets.py
+++ b/widgets.py
@@ -11,7 +11,7 @@
 from django.contrib.admin import widgets as admin_widgets
 from django.core.urlresolvers import reverse
 from django.forms.widgets import flatatt
-from django.forms.util import smart_unicode
+from django.utils.encoding import smart_unicode
 from django.utils.html import escape
 from django.utils import simplejson
 from django.utils.datastructures import SortedDict
EOF
```

Even though we have previously installed Debian-provided python-django 1.4 outside the virtualenv and we set it up with `--system-site-packages`, `pip` will happily install Django 1.2 inside:

```
(old_djnro)# pip install Django==1.2.3
[...]
Installing collected packages: Django
  Found existing installation: Django 1.4.5
    Not uninstalling Django at /usr/lib/python2.7/dist-packages, outside environment /srv/venv/old_djnro
[...]
```

#### *New* virtualenv

- `South==1.0`
- `django-registration==1.0`
- `django-tinymce==1.5.3`
- `ipaddr==2.1.11`
- `oauth==1.0.1`
- `longerusername==0.4`
- `python-social-auth==0.2.10`
- `requests==2.7.0` (also required by PSA)

### Installing DjNRO and migrating data

After creating the virtual environments and installing the required packages in each one, these are the steps to install both the old and new versions of DjNRO and migrate the data as necessary:

* Clone the DjNRO repo and checkout the `old-stable` branch:
  `git clone --branch old-stable https://github.com:grnet/djnro.git`
* Modify `manage.py` so that it will use the virtualenv python interpreter: change the first line from `#!/usr/bin/python` to `#!/usr/bin/env python`
* Copy `settings.py`, `urls.py` and `django.wsgi` over from the old host, adjusting any paths therein as necessary for matching the installation of DjNRO on the new host.
* Create the MySQL database (and grant rights to the DjNRO user as on the old host):
  `create database eduroam character set = 'utf8' collate = 'utf8_unicode_ci';`
* Activate the *old* virtualenv:
  `source /path/to/old-virtualenv/bin/activate`
* Create the DjNRO schema and run South migrations:
  `./manage.py syncdb --setings='settings'`
  `./manage.py migrate --settings='settings'`
* Dump DjNRO data on the **old** host:
  `./manage.py dumpdata --indent=4 --natural --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_production.json`
  **Note:** The `contenttypes` app and `auth.Permission` model were excluded because they are not necessary (they are recreated by `syncdb`) and they could not be properly imported on the new host. If there are custom permissions assignments, however, they would be lost.
* Copy over the JSON data dump to the **new** host and reorder the *fixtures*, so that e.g. a model having a foreign key to another model will be re-created after the latter upon import:

```
./manage.py reorder_fixtures --settings='settings' /tmp/eduroam_production.json \
    edumanage.name_i18n \
    edumanage.url_i18n \
    edumanage.contact \
    edumanage.realm \
    edumanage.realmdata \
    edumanage.institution \
    edumanage.institutiondetails \
    edumanage.institutioncontactpool \
    edumanage.serviceloc \
    edumanage.instserver \
    edumanage.instrealm \
    edumanage.instrealmmon \
    edumanage.monlocalauthnparam \
    edumanage.monproxybackclient \
    > /tmp/eduroam_production.ordered.json
```

* Import the reordered data:
  `./manage.py loaddata --settings='settings' /tmp/eduroam_production.ordered.json`
* Copy over the apache vhost and adjust as necessary.
* Verify that the old version of DjNRO is running and data has been properly imported.
* Before switching to the new version of DjNRO, undo the modification to `manage.py`:
  `git checkout -- manage.py`
* Checkout the target version:
  `git checkout master`
* Create `djnro/local_settings.py` by copying `djnro/local_settings.py.dist` and adjusting it according to `settings.py`.
* Activate the *new* virtualenv:
  `source /path/to/new-virtualenv/bin/activate`
* *Fake* the initial migration for PSA because we are migrating from Django Social Auth:
  `./manage.py migrate default 0001_initial --fake`
* Run the rest of the migrations:
  `./manage.py migrate`
* Modify/update the apache vhost configuration as necessary.
* Verify that the new version of DjNRO is running and data has been properly migrated.
