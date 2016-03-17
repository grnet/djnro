# Upgrading DjNRO from 1.0 to 1.1 or later

DjNRO 1.0 was developed with django 1.4. Version 1.1 was updated for django 1.8.9

Django 1.8 has switched from the South migrations framework to built-in
migrations.  A large part of the upgrade is handling the transition from South
to Django migrations.

## Backup data

Dump data with the help of south (always keep a backup):

	./manage.py dumpdata --indent=4 --natural --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_1.0.json

And, possibly, make also a full database dump from your database, and also make
an archive of your installation tree - to be able to revert if something goes
wrong.


## Update older DjNRO to latest 1.0

There were some data changes introduced to the data model in the DjNRO code prior to the upgrade to Django 1.8 migration.

Get the latest 1.0 DjNRO code:

    # TODO: we need this tag in the repository
    git checkout djnro-1.0.0

And run the database migrations:

    ./manage.py migrate

## Install DjNro

Install DjNRO >= v1.1 by following the installation instructions - configuring it to use the same database.


## Migrate

### User Model changes

Because of the South to Django migrations change, and other changes in Django, we are no longer using the ````longerusername```` module to extend the username length - and are instead using a Custom User Model, accounts.Auth.

To preserve identities of existing user (and permissions and django log entries related to users), we rename the entry in the Django ````contenttypes```` table.  Launch the Django management shell with ````./manage.py shell```` and run the following commands:

    from django.contrib.contenttypes.models import ContentType
    ct=ContentType.objects.get(model='user')
    ct.app_label=u'accounts'
    ct.save()

It is important to perform this change before running the ````./manage.py
migrate```` command in any form of invocation. Otherwise, the migrate command
would create new ````ContentType```` entries for ````accounts.User```` that
would conflict with renaming the existing ````auth.User```` entries.

### Switch to Django migrations

Next, we need to:
* Tell the Django migrations framework that our database structures (as of final 1.0, so the current initial release) are already in place
* But replay all migrations that Django internal structures have undergone between Django 1.4 and 1.8
* And this applies also to the User model that is now presented under (our) accounts package.

The following sequence does the right thing:
* Introduce initial structures as already present for ````contenttypes````, ````auth````, ````edumanage```` and ````accounts```` packages (````edumanage```` and ````accounts```` only up to ````0001_initial```` and ````0002_initial```` respectively).
* Apply all subsequent migrations (last line)

````
./manage.py migrate --fake-initial contenttypes
./manage.py migrate --fake-initial auth
./manage.py migrate --fake-initial --fake edumanage 0001_initial
./manage.py migrate --fake-initial --fake accounts 0002_initial
./manage.py migrate --fake-initial
````

## Fix up database

There are two minor differences that your migrated database may have compared to a newly generated one:

1. SocialAuth.Nonce may be missing a UNIQUE CONSTRAINT.  The South migrations generated for SocialAuth somehow miss the constraint, Django migrations have it.  You can fix it up by adding manually the constraint: this is the PostgreSQL syntax:

        ALTER TABLE social_auth_nonce ADD CONSTRAINT "social_auth_nonce_server_url_36601f978463b4_uniq" UNIQUE (server_url, timestamp, salt);

2. Edumanage.Instrealmmon may be missing a FOREIGN_KEY constraint if you created your database on PostgreSQL before the full for PostgreSQL-specific fix was retroactively applied to ````edumanage/migrations/0022_auto__chg_field_institutiondetails_number_id__del_field_instrealmmon_i.py```` in commit 28f60f6233b14c9b16d5aae12b8cbc0b39477e08.  Fix this by running:

        ALTER TABLE edumanage_instrealmmon ADD CONSTRAINT "edumanage_i_realm_id_24cc89d4be4145e5_fk_edumanage_instrealm_id" FOREIGN KEY (realm_id) REFERENCES edumanage_instrealm(id) DEFERRABLE INITIALLY DEFERRED;

If the command fails with an error message saying the constraint already exists, the error message can be safely ignored - it means this erroneous condition has not occurred on this database.

# Loading old data to a new instance
In case you want to load data to a new database one has to follow these extra
steps.
In the old installation of DjNRO:

 - install and add 'fixture_magic' to INSTALLED_APPS in settings.py
 - run:

 		./manage.py reorder_fixtures --settings='settings' /tmp/eduroam_1.0.json edumanage.name_i18n edumanage.url_i18n edumanage.contact edumanage.realm edumanage.realmdata edumanage.institution edumanage.institutiondetails edumanage.institutioncontactpool edumanage.serviceloc edumanage.instserver edumanage.instrealm edumanage.instrealmmon edumanage.monlocalauthnparam edumanage.monproxybackclient > /tmp/eduroam_1.0.ordered.json


Now in the new installation:

 - run `./manage.py loaddata --settings='settings' /tmp/eduroam_1.0.ordered.json`
 - Continue with the `Migrate` step from above.

