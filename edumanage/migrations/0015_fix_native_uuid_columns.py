# -*- coding: utf-8 -*-
from django.db import migrations


def fix_native_uuid_columns(apps, schema_editor):
    """
    Django 5.0+ uses a native `uuid` column for UUIDField on MariaDB 10.7+
    (has_native_uuid_field), instead of the char(32) hex representation used
    everywhere else. Databases whose edumanage_institution/edumanage_serviceloc
    tables were created before the server was upgraded to MariaDB 10.7+ still
    have the old char(32) columns, which are too short for the value Django
    now sends (a 36-character dashed UUID), causing "Data too long" errors.
    No-op on any backend/version where this mismatch cannot occur.
    """
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return
    if not connection.features.has_native_uuid_field:
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE edumanage_institution MODIFY instid uuid NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE edumanage_serviceloc MODIFY locationid uuid NOT NULL"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('edumanage', '0014_remove_obsolete_registration_profile_table'),
    ]

    operations = [
        migrations.RunPython(fix_native_uuid_columns, migrations.RunPython.noop),
    ]
