from django.db import migrations


def drop_table(apps, schema_editor):
    table_name = schema_editor.connection.ops.quote_name('registration_registrationprofile')
    schema_editor.execute(f"DROP TABLE IF EXISTS {table_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('django_registration', '0001_initial'),
        ('edumanage', '0013_instserver_psk'),
    ]

    operations = [
        migrations.RunPython(drop_table, reverse_code=migrations.RunPython.noop),
    ]
