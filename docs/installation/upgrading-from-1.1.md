# Upgrading DjNRO from 1.1 to 1.2 or later

DjNRO 1.1 targeted Django 1.8. Version 1.2 was updated for Django 1.11

The main change in the Django 1.11 update is that the `python-social-auth` package was split into `social-auth-core` and `social-auth-app-django`.

This affects the database (see the following section on migrations) and `MANAGE_LOGIN_METHODS` in `local_settings.py`, where you must replace `social` namespace with `social_core`.

Additionally, the `TEMPLATES_DEBUG` setting has been removed and template debugging is controlled by `DEBUG` -- this was already the default for `TEMPLATE_DEBUG` in `local_settings.py`.

DjNRO 1.2 also includes the adaptation for eduroam database version 2. See the respective section that follows for some important implementation notes.

Finally, this version includes more languages and translations (Spanish,
Romanian). You can restrict the available translations by overriding
`LANGUAGES` in `local_settings.py`.

## Backup data

Dump data (always keep a backup):

    ./manage.py dumpdata --indent=4 --natural-foreign --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_1.1.json

And, possibly, also make a full database dump from your database, as well as
an archive of your installation tree -- to be able to revert if something goes
wrong.


## Install DjNRO

Install DjNRO >= v1.2 by following the installation instructions -- configuring it to use the same database.


## Migrate

### Social Auth Core

The `python-social-auth` package has been split into
`social-auth-core` and `social-auth-app-django`. The latter package
carried over database migrations from the older package, however the
Django app was renamed twice in the splitting process: `default` to
`social_auth` and then to `social_django`. For this reason these migrations
are declared as replacements for the corresponding migrations under
the deprecated application names. However Django requires that all
such migrations are recorded as having been applied, or else it will not
consider the migrations carried over in `social-auth-app-django` as
having been applied. If that happens, you will come across this
seemingly irrelevant error while running migrations:

```python
KeyError: ('social_django', u'usersocialauth')
```

There are two alternative workarounds for this issue:

* Install the last version (before the split) of `python-social-auth`
**before** installing DjNRO v1.2 and run migrations:

      # if you are using an older version of pip, you may need to run it
      # with --index-url=https://pypi.python.org/simple/
      pip install python-social-auth==0.2.21
      ./manage.py migrate

* After installing DjNRO v1.2, run `./manage.py shell` and use the
following commands to get the migrations recorded in the database as
having been applied:

```python
from django.db.migrations.recorder import MigrationRecorder
for m in MigrationRecorder.Migration.objects.filter(app='default'):
    if not MigrationRecorder.Migration.objects.filter(app='social_auth', name=m.name):
        print("Recording migration default:%s as social_auth:%s" % (m.name, m.name))
        m_social=MigrationRecorder.Migration(app='social_auth', name=m.name)
        m_social.save()
```

After applying either of these workarounds you can then run `./manage.py migrate`.

## Implementation notes: eduroam database version 2 adaptation

Please consider the following notes and caveats with regard to the eduroam
database version 2 adaptation:

* `UUID` is enforced for `Institution.instid`, `ServiceLoc.locationid`.
  Such fields are not editable through forms, while
  `parse_institution_xml` defaults to deriving a `UUID` by means of MD5
  hashing, if the input is unsuitable.
  * If you want parsing to fail, skipping the corresponding `location`
    element, use `--no-derive-uuids-with-md5` instead.
* `Coordinates` are modeled as many-to-many for `ServiceLoc`, but only a single
  set is supported currently (this is enforced by a signal receiver).
  `ServiceLoc` maintains longitude, latitude attributes as proxy (cached)
  properties to the related `Coordinates` object. On the other hand,
  `parse_institution_xml` retains the first set of coordinates it encounters
  in a location, printing a warning if more are found.
* `Coordinates` are currently ignored in institution edit form, nor are
  they otherwise presented anywhere, while they are processed by
  `parse_institution_xml` as expected.
  * Other than the latter, altitude is thus currently ignored.
* Data migration from `ServiceLoc.wired` to `ServiceLoc.wired_no` is
  driven by `settings.SERVICELOC_DERIVE_WIRED_NO`, which defaults to
  mapping `True` to 42. You can override this in `local_settings.py`, for
  example:

```python
EXTRA_SERVICELOC_DERIVE_WIRED_NO = {
    True: 123,
}
```

* Compatibility with all eduroam database versions is retained
  throughout db views and `parse_institution_xml`. For the latter the
  version may be provided through a command-line option. For the former
  the requested version is inferred by considering path, query parameter
  or resource (realm vs. ro). If no version is specified/hinted, a
  default is used, which, as of now, is version 2. In order to revert to
  version 1, add the following to `local_settings.py`:

```python
from utils.edb_versioning import EduroamDatabaseVersionDef
EXTRA_EDUROAM_DATABASE_VERSIONS = {
    'default': EduroamDatabaseVersionDef.version_1,
}
```

## See Also

The guide for [upgrading from 1.0](upgrading-from-1.0.md) may also prove helpful for migrating from older versions of DjNRO to 1.1.
