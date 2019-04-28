# Upgrading DjNRO from 1.1 to 1.2 or later

DjNRO 1.1 targeted Django 1.8. Version 1.2 was updated for Django 1.11

The main change in the Django 1.11 update is that the `python-social-auth` package was split into `social-auth-core` and `social-auth-app-django`.

This affects the database (see the following section on migrations) and `MANAGE_LOGIN_METHODS` in `local_settings.py`, where you must replace `social` namespace with `social_core`.

Additionally, the `TEMPLATES_DEBUG` setting has been removed and template debugging is controlled by `DEBUG` -- this was already the default for `TEMPLATE_DEBUG` in `local_settings.py`.

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

    KeyError: ('social_django', u'usersocialauth')

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

    from django.db.migrations.recorder import MigrationRecorder
    for m in MigrationRecorder.Migration.objects.filter(app='default'):
        if not MigrationRecorder.Migration.objects.filter(app='social_auth', name=m.name):
            print("Recording migration default:%s as social_auth:%s" % (m.name, m.name))
            m_social=MigrationRecorder.Migration(app='social_auth', name=m.name)
            m_social.save()

After applying either of these workarounds you can then run `./manage.py migrate`.

## See Also

The guide for [upgrading from 1.0](upgrading-from-1.0.md) may also prove helpful for migrating from older versions of DjNRO to 1.1.
