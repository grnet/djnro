# Upgrading DjNRO from 1.2 to 1.3 or later

**NOTE**: You **must** use Python version 3.10 or later for this update to work. This is due to the version of the `social-auth-app-django` package used in the project.

DjNRO 1.3 marks a significant upgrade to the Django framework version used.

If you are upgrading from DjNRO version 1.1 or earlier to version 1.3, we recommend following the version 1.2 upgrade guide first, before returning to this guide. Earlier documents contain solutions to changes created by the splitting of the `python-social-auth` package.

## Changes made

### Django version update

DjNRO version 1.2 used Django. DjNRO version 1.3 makes a significant jump from Django version 1.11 to Django version 4.2. This means DjNRO will receive Django security updates until April 2026.

### Package version consistency

All pip packages defined in *requirements.txt* and *requirements-optional.txt* now use either fixed versions or compatible versions for improved stability.

### Clickjacking protection

DjNRO 1.3 adds clickjacking protection via Django's `XFrameOptionsMiddleware` middleware.

### Enhanced RADIUS configurations for servers

Configured servers now have two additional options to select from under the *Protocol* option.

#### RADIUS over TLS (RadSec, RFC6614)

This option enables more secure RADIUS communication using transport layer security (TLS) as defined by [RFC 6614](https://datatracker.ietf.org/doc/html/rfc6614)

#### Radius over TLS (PSK)

This option enables more secure RADIUS communication using TLS protected with a pre-shared key (PSK). This requires an additonal option in *local_settings.py.dist* to be configured.

**NOTE:** A new setting has been added to *local_settings.py.dist* that relates to this option. More deatails are available [here](#radius-over-tls-psk-settings).

### New layout for the Manage page

The *Manage* login page has had its title updated from *Login* to *Login to Management Pages*, in order to clarify the page's purpose.

Additionally, a new message has been added to the page that contains a hyperlink to `NRO_DOMAIN_MAIN_URL`. Please refer to [NRO_DOMAIN_MAIN_URL](#nro_domain_main_url) for more information.

### Caching changes

The obsolete `MemcacheCache` backend has been replaced with the `PyMemcacheCache` backend in local settings. To update your local settings, please follow the instructions [here](#cache-configuration-changes).

### Middleware updates

The third-party `RemoveUnneededVaryHeadersMiddleware` middleware has been removed.

### Venue info configuration change

Venue info can now be specified from a list of descriptive messages instead of specifying a numerical code. For example, instead of specifying *2,7*, you can select *Professional Office* from a drop-down menu. This removes the need to look up the definition of each code.

### Contact type

Contacts can now be set to *service/department* or *person*.

### Contact privacy

Contacts can now be set to *private* or *public*.

### Participant display changes

Only participants marked as active will be displayed under *Participating Institutions* from now on.

### Timestamp fixes for InstServer and ServiceLoc

Timestamps (*ts*) on the `InstServer` and `ServiceLoc` objects are now updated on every change, including changes to subordinate objects like `Contact`. This ensures that such changes are picked up by the eduroam database.

### Realm-server configuration (administrative users only)

DjNRO 1.3 adds the RealmServer model, which allows recording RADIUS servers operated by the NRO for the country-level Realm and exposing them in the Roaming Operator data export.
This allows the NRO to get RadSec certificates issued by eduPKI via the admin interface in eduroam CAT.

As the RealmServers will be configured only by the NRO admin, there are no dedicated UI pages for the RealmServers and they can only be managed via the Django admin pages.

## Configuration file changes

The file *local_settings.py.dist* has new settings added. Please configure these before deploying the upgraded software.

### Cache configuration changes

If you are using the default `MemcacheCache` backend for caching, this must change to `PyMemcacheCache`. Please refer to [Cache Configuration (DjNRO Version 1.3 and Later)](install.md) in the installation instructions for more details.

### NRO_DOMAIN_MAIN_URL

The setting `NRO_DOMAIN_MAIN_URL` in the file *local_settings.py.dist* now has an additional use. The *Manage* tab now contains a message with a hyperlink to `NRO_DOMAIN_MAIN_URL`. This message will inform users that may have naviated to the *Manage* login page by mistake to click on this hyperlink.

### RADIUS over TLS (PSK) settings

If you need to support RADIUS-TLS-PSK connections, then you must set the variable `NRO_TLSPSK_REALM` in the file *local_settings.py.dist*. This setting is used to generate a TLS-PSK identity for connections from eduroam SPs. It must be set to the realm you wish to use.

### CAT Enrollment Changes

The default values for several Configuration Assistant Tool (CAT) related settings has been updated. If you have uncommented any of these sections from *local_settings.py.dist* without changing their default values, please update the default values as specified. The following values have changed:

#### Production default changes

* `CAT_IDPMGMT_URL` has been changed from *https://cat.eduroam.org/admin/overview_idp.php* to *https://cat.eduroam.org/admin/overview_org.php*

#### Testing default changes

* `CAT_API_URL` has been changed from *https://cat-test.eduroam.org/test/admin/API.php* to *https://cat-test.eduroam.org/admin/API.php*

* `CAT_USER_API_URL` has been changed from *https://cat-test.eduroam.org/test/user/API.php* to *https://cat-test.eduroam.org/user/API.php*

* `CAT_USER_API_LOCAL_DOWNLOADS` has been changed from *https://cat-test.eduroam.org/test/* to *https://cat-test.eduroam.org/*
* `CAT_PROFILES_URL` has been changed from *https://cat-test.eduroam.org/test* to *https://cat-test.eduroam.org/*
* `CAT_IDPMGMT_URL` has been changed from *https://cat-test.eduroam.org/test/admin/overview_idp.php* to *https://cat-test.eduroam.org/admin/overview_org.php*

## Backing up database

Run the following command to dump database contents in a form that Django can restore:

    ./manage.py dumpdata --indent=4 --natural-foreign --exclude=contenttypes --exclude=auth.Permission > /tmp/eduroam_1.2.json

You may also wish to generate a full database dump as an extra precaution, or create a full copy of your installation tree. These methods will add an extra level of protection against upgrade failures, as they will let you more fully recover a broken applicaiton.

## Install DjNRO

Install DjNRO >= v1.3 by following the installation instructions and configuring it to use the same database.

## Database migrations

The following migrations were added or significantly modified between DjNRO version 1.2 and 1.3:

* `accounts/migrations/0005_auto_20250211_1352.py`
* `accounts/migrations/0006_alter_user_first_name.py` 
* `edumanage/migrations/0011_edb21_server_schema.py`
* `edumanage/migrations/0012_venue_info_select.py`
* `edumanage/migrations/0013_instserver_psk.py`

Some existing migrations were also modified, so it is still recommended to run all migrations again.

To run all migrations, use the following command:

```
./manage.py migrate
```

## Static files

As with every upgrade, it is necessary to *collect* static files
from DjNRO and other sources to the folder the HTTP server will serve
them from. See the particular section in the chapter
[Installing DjNRO](install.md).

