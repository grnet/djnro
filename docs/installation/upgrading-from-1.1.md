# Upgrading DjNRO from 1.1 to 1.2 or later

DjNRO 1.1 was running with django 1.8. Version 1.2 was updated for django 1.11

The main change in the Django 1.11 upgrade is that the `python-social-auth` package is replaced with `social-auth-core`.

This has effects on the database (see section on migrations below), and also affects `local_settings.py` (replace `social` namespace with `social_core`)

Additionally, the `TEMPLATES_DEBUG` setting has been removed and template debugging is controlled by `DEBUG` - which was the default for `TEMPLATE_DEBUG` in `local_settings.py` anyway.

## Backup data

Dump data (always keep a backup):

	./manage.py dumpdata --indent=4 --natural --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_1.1.json

And, possibly, make also a full database dump from your database, and also make
an archive of your installation tree - to be able to revert if something goes
wrong.


## Install DjNRO

Install DjNRO >= v1.2 by following the installation instructions - configuring it to use the same database.


## Migrate

### Social Auth Core

The `python-social-auth` package has been renamed to `social-auth-core` (and has had sigificant changes done to it afterwards).

The `social-auth-core` package has kept the same sequence of database migration steps, but because of the rename, Django would get confused and would try applying the migrations from start ... which would fail, because the tables already exist.

Apply the following workaround: change the package name in the migrations history to make Django Migrations think these have been applied under the new package name.   (Because of the hierarchy used in the old package versions, the migrations were recorded as belonging to package `default`).  Run `./manage.py shell` and paste in the following code:

    from django.db.migrations.recorder import MigrationRecorder
    for m in MigrationRecorder.Migration.objects.filter(app='default'):
        if not MigrationRecorder.Migration.objects.filter(app='social_auth', name=m.name):
            print("Recording migration default:%s as social_auth:%s" % (m.name, m.name))
            m_social=MigrationRecorder.Migration(app='social_auth', name=m.name)
            m_social.save()
    exit()

After applying this workaround, you can safely run `./manage.py migrate`.

## See Also

The guide for [upgrading from 1.0](upgrading-from-1.0.md) may also prove helpful for migrating from older versions of DjNRO to 1.1.
