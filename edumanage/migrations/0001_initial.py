# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import edumanage.models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CatEnrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cat_inst_id', models.PositiveIntegerField()),
                ('url', models.CharField(help_text=b'Set to ACTIVE if institution has CAT profiles', max_length=255, null=True, blank=True)),
                ('cat_instance', models.CharField(max_length=50, choices=edumanage.models.get_choices_from_settings('CAT_INSTANCES'))),
                ('ts', models.DateTimeField(auto_now=True)),
                ('applier', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_column=b'contact_name')),
                ('email', models.CharField(max_length=80, db_column=b'contact_email')),
                ('phone', models.CharField(max_length=80, db_column=b'contact_phone')),
            ],
            options={
                'verbose_name': 'Contact',
                'verbose_name_plural': 'Contacts',
            },
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ertype', models.PositiveIntegerField(db_column=b'type', choices=[(1, b'IdP only'), (2, b'SP only'), (3, b'IdP and SP')])),
            ],
        ),
        migrations.CreateModel(
            name='InstitutionContactPool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contact', models.OneToOneField(to='edumanage.Contact')),
                ('institution', models.ForeignKey(to='edumanage.Institution')),
            ],
            options={
                'verbose_name': 'Instutution Contact (Pool)',
                'verbose_name_plural': 'Instutution Contacts (Pool)',
            },
        ),
        migrations.CreateModel(
            name='InstitutionDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address_street', models.CharField(max_length=96)),
                ('address_city', models.CharField(max_length=64)),
                ('oper_name', models.CharField(help_text='The primary, registered domain name for your institution, eg. example.com.<br>This is used to derive the Operator-Name attribute according to RFC5580, par.4.1, using the REALM namespace.', max_length=24, null=True, blank=True)),
                ('number_user', models.PositiveIntegerField(help_text='Number of users (individuals) that are eligible to participate in eduroam service', null=True, blank=True)),
                ('number_id', models.PositiveIntegerField(help_text='Number of issued e-identities (credentials) that may be used for authentication in eduroam service', null=True, blank=True)),
                ('ts', models.DateTimeField(auto_now=True)),
                ('contact', models.ManyToManyField(to='edumanage.Contact')),
                ('institution', models.OneToOneField(to='edumanage.Institution')),
            ],
            options={
                'verbose_name': "Institutions' Details",
                'verbose_name_plural': 'Institution Details',
            },
        ),
        migrations.CreateModel(
            name='InstRealm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('realm', models.CharField(max_length=160)),
                ('instid', models.ForeignKey(verbose_name=b'Institution', to='edumanage.Institution')),
            ],
            options={
                'verbose_name': 'Institution Realm',
                'verbose_name_plural': "Institutions' Realms",
            },
        ),
        migrations.CreateModel(
            name='InstRealmMon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mon_type', models.CharField(max_length=16, choices=[(b'localauthn', b'Institution provides account for the NRO to monitor the realm')])),
                ('realm', models.ForeignKey(to='edumanage.InstRealm')),
            ],
            options={
                'verbose_name': 'Institution Monitored Realm',
                'verbose_name_plural': 'Institution Monitored Realms',
            },
        ),
        migrations.CreateModel(
            name='InstServer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ertype', models.PositiveIntegerField(db_column=b'type', choices=[(1, b'IdP only'), (2, b'SP only'), (3, b'IdP and SP')])),
                ('name', models.CharField(help_text='Descriptive label', max_length=80, null=True, blank=True)),
                ('addr_type', models.CharField(default=b'ipv4', max_length=16, choices=[(b'any', b'Default'), (b'ipv4', b'IPv4 only')])),
                ('host', models.CharField(help_text='IP address | FQDN hostname', max_length=80)),
                ('rad_pkt_type', models.CharField(default=b'auth+acct', max_length=48, null=True, blank=True, choices=[(b'auth', b'Handles Access-Request packets only'), (b'acct', b'Handles Accounting-Request packets only'), (b'auth+acct', b'Handles both Access-Request and Accounting-Request packets')])),
                ('auth_port', models.PositiveIntegerField(default=1812, help_text='Default for RADIUS: 1812', null=True, blank=True)),
                ('acct_port', models.PositiveIntegerField(default=1813, help_text='Default for RADIUS: 1813', null=True, blank=True)),
                ('status_server', models.BooleanField(help_text='Do you accept Status-Server requests?')),
                ('secret', models.CharField(max_length=80)),
                ('proto', models.CharField(default=b'radius', max_length=12, choices=[(b'radius', b'traditional RADIUS over UDP')])),
                ('ts', models.DateTimeField(auto_now=True)),
                ('instid', models.ManyToManyField(default=b'none', related_name='servers', to='edumanage.Institution')),
            ],
            options={
                'verbose_name': 'Institution Server',
                'verbose_name_plural': "Institutions' Servers",
            },
        ),
        migrations.CreateModel(
            name='MonLocalAuthnParam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('eap_method', models.CharField(max_length=16, choices=[(b'PEAP', b'EAP-PEAP'), (b'TTLS', b'EAP-TTLS')])),
                ('phase2', models.CharField(max_length=16, choices=[(b'PAP', b'PAP'), (b'CHAP', b'CHAP'), (b'MS-CHAPv2', b'MS-CHAPv2')])),
                ('username', models.CharField(max_length=36)),
                ('passwp', models.CharField(max_length=80, db_column=b'pass')),
                ('instrealmmonid', models.OneToOneField(to='edumanage.InstRealmMon')),
            ],
            options={
                'verbose_name': 'Monitored Realm (local authn)',
                'verbose_name_plural': 'Monitored Realms (local authn)',
            },
        ),
        migrations.CreateModel(
            name='MonProxybackClient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Descriptive label', max_length=80, null=True, blank=True)),
                ('host', models.CharField(help_text='IP address | FQDN hostname', max_length=80)),
                ('status_server', models.BooleanField()),
                ('secret', models.CharField(max_length=80)),
                ('proto', models.CharField(max_length=12, choices=[(b'radius', b'traditional RADIUS over UDP')])),
                ('ts', models.DateTimeField(auto_now=True)),
                ('instrealmmonid', models.ForeignKey(to='edumanage.InstRealmMon')),
            ],
            options={
                'verbose_name': 'Institution Proxyback Client',
                'verbose_name_plural': 'Institution Proxyback Clients',
            },
        ),
        migrations.CreateModel(
            name='Name_i18n',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('lang', models.CharField(max_length=5, choices=edumanage.models.get_choices_from_settings('URL_NAME_LANGS'))),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Name (i18n)',
                'verbose_name_plural': 'Names (i18n)',
            },
        ),
        migrations.CreateModel(
            name='Realm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=5, choices=edumanage.models.get_choices_from_settings('REALM_COUNTRIES'))),
                ('stype', models.PositiveIntegerField(default=0, editable=False)),
                ('address_street', models.CharField(max_length=32)),
                ('address_city', models.CharField(max_length=24)),
                ('ts', models.DateTimeField(auto_now=True)),
                ('contact', models.ManyToManyField(to='edumanage.Contact')),
            ],
            options={
                'verbose_name': 'Realm',
                'verbose_name_plural': 'Realms',
            },
        ),
        migrations.CreateModel(
            name='RealmData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number_inst', models.PositiveIntegerField(editable=False)),
                ('number_user', models.PositiveIntegerField(editable=False)),
                ('number_id', models.PositiveIntegerField(editable=False)),
                ('number_IdP', models.PositiveIntegerField(editable=False)),
                ('number_SP', models.PositiveIntegerField(editable=False)),
                ('number_IdPSP', models.PositiveIntegerField(editable=False)),
                ('ts', models.DateTimeField(editable=False)),
                ('realmid', models.OneToOneField(to='edumanage.Realm')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceLoc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('longitude', models.DecimalField(max_digits=12, decimal_places=8)),
                ('latitude', models.DecimalField(max_digits=12, decimal_places=8)),
                ('address_street', models.CharField(max_length=96)),
                ('address_city', models.CharField(max_length=64)),
                ('SSID', models.CharField(max_length=16)),
                ('enc_level', edumanage.models.MultiSelectField(blank=True, max_length=64, null=True, choices=[(b'WPA/TKIP', b'WPA-TKIP'), (b'WPA/AES', b'WPA-AES'), (b'WPA2/TKIP', b'WPA2-TKIP'), (b'WPA2/AES', b'WPA2-AES')])),
                ('port_restrict', models.BooleanField()),
                ('transp_proxy', models.BooleanField()),
                ('IPv6', models.BooleanField()),
                ('NAT', models.BooleanField()),
                ('AP_no', models.PositiveIntegerField()),
                ('wired', models.BooleanField()),
                ('ts', models.DateTimeField(auto_now=True)),
                ('contact', models.ManyToManyField(to='edumanage.Contact', blank=True)),
                ('institutionid', models.ForeignKey(verbose_name=b'Institution', to='edumanage.Institution')),
            ],
            options={
                'verbose_name': 'Service Location',
                'verbose_name_plural': 'Service Locations',
            },
        ),
        migrations.CreateModel(
            name='URL_i18n',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=180, db_column=b'URL')),
                ('lang', models.CharField(max_length=5, choices=edumanage.models.get_choices_from_settings('URL_NAME_LANGS'))),
                ('urltype', models.CharField(max_length=10, db_column=b'type', choices=[(b'info', b'Info'), (b'policy', b'Policy')])),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Url (i18n)',
                'verbose_name_plural': 'Urls (i18n)',
            },
        ),
        migrations.AddField(
            model_name='instrealm',
            name='proxyto',
            field=models.ManyToManyField(help_text='Only IdP and IdP/SP server types are allowed', to='edumanage.InstServer'),
        ),
        migrations.AddField(
            model_name='institution',
            name='realmid',
            field=models.ForeignKey(to='edumanage.Realm'),
        ),
        migrations.AddField(
            model_name='catenrollment',
            name='inst',
            field=models.ForeignKey(to='edumanage.Institution'),
        ),
        migrations.AlterUniqueTogether(
            name='instrealmmon',
            unique_together=set([('realm', 'mon_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='catenrollment',
            unique_together=set([('inst', 'cat_instance')]),
        ),
    ]
