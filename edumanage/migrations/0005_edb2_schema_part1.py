# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-31 06:34
from __future__ import unicode_literals

import uuid
from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import edumanage.models

from . import AppAwareRunPython

class Backfill(object):
    def __init__(self, model, field, value_func, only_fill_null=True):
        self.model = model
        self.field = field
        self.value_func = value_func
        self.only_fill_null = only_fill_null
    def __call__(self, apps, schema_editor, app_label):
        model = apps.get_model(app_label, self.model)
        rows = model.objects.all()
        if self.only_fill_null:
            filter_kwargs = {'{}__isnull'.format(self.field): True}
            rows = rows.filter(**filter_kwargs)
        for row in rows:
            setattr(row, self.field, self.value_func())
            row.save(update_fields=[self.field])


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('edumanage', '0004_auto__chg_field_name_i18n_name__increase_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address_i18n',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('lang', models.CharField(choices=edumanage.models.get_choices_from_settings('URL_NAME_LANGS'), max_length=5)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Address (i18n)',
                'verbose_name_plural': 'Addresses (i18n)',
            },
        ),
        migrations.RemoveField(
            model_name='realm',
            name='stype',
        ),
        migrations.AddField(
            model_name='contact',
            name='privacy',
            field=models.PositiveIntegerField(choices=[(0, 'private'), (1, 'public')], db_column='contact_privacy', default=0),
        ),
        migrations.AddField(
            model_name='contact',
            name='type',
            field=models.PositiveIntegerField(choices=[(0, 'person'), (1, 'service/department')], db_column='contact_type', default=0),
        ),
        migrations.AddField(
            model_name='institution',
            name='stage',
            field=models.PositiveIntegerField(choices=[(0, 'preproduction/test'), (1, 'active')], default=1),
        ),
        migrations.AddField(
            model_name='institutiondetails',
            name='venue_info',
            field=models.CharField(blank=True, db_column='inst_type', help_text='IEEE 802.11-2012, clause 8.4.1.34 Venue Info. This is a pair of integers, each between 0 and 255, separated with ",".', max_length=7, validators=[edumanage.models.validate_venue_info]),
        ),
        migrations.AddField(
            model_name='realm',
            name='roid',
            field=models.CharField(db_column='ROid', default=getattr(settings, 'NRO_ROID'), max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='realm',
            name='stage',
            field=models.PositiveIntegerField(choices=[(0, 'preproduction/test'), (1, 'active')], default=1),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='geo_type',
            field=models.PositiveIntegerField(choices=[(0, 'single spot'), (1, 'area'), (2, 'mobile')], db_column='type', default=0),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='enc_level',
            field=edumanage.models.MultiSelectField(blank=True, choices=[('WPA/TKIP', 'WPA-TKIP'), ('WPA/AES', 'WPA-AES'), ('WPA2/TKIP', 'WPA2-TKIP'), ('WPA2/AES', 'WPA2-AES'), ('WPA3/AES', 'WPA3-AES')], max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='operation_hours',
            field=models.CharField(blank=True, help_text='Free text description of opening hours, if service is not available 24 hours per day', max_length=255),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='physical_avail',
            field=models.PositiveIntegerField(choices=[(0, 'no restrictions'), (1, 'physical access restrictions')], db_column='availability', default=0, help_text='Restrictions regarding physical access to the service area'),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='stage',
            field=models.PositiveIntegerField(choices=[(0, 'preproduction/test'), (1, 'active')], default=1),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='tag',
            field=edumanage.models.MultiSelectField(blank=True, choices=[('port_restrict', 'port restrictions'), ('transp_proxy', 'transparent proxy'), ('IPv6', 'IPv6'), ('NAT', 'NAT'), ('HS2.0', 'Passpoint (Hotspot 2.0)')], max_length=64),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='venue_info',
            field=models.CharField(blank=True, db_column='location_type', help_text='IEEE 802.11-2012, clause 8.4.1.34 Venue Info. This is a pair of integers, each between 0 and 255, separated with ",".', max_length=7, validators=[edumanage.models.validate_venue_info]),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='wired_no',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='AP_no',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='institutiondetails',
            name='address_street',
            field=models.CharField(max_length=96, null=True),
        ),
        migrations.AlterField(
            model_name='institutiondetails',
            name='address_city',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='realm',
            name='address_street',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='realm',
            name='address_city',
            field=models.CharField(max_length=24, null=True),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='address_city',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='address_street',
            field=models.CharField(max_length=96, null=True),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='IPv6',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='NAT',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='port_restrict',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='transp_proxy',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='wired',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='institution',
            name='instid',
            field=models.UUIDField(default=None, null=True),
        ),
        AppAwareRunPython(
            Backfill('institution', 'instid', uuid.uuid4),
            reverse_code=AppAwareRunPython.noop,
            hints={'model_name': 'institution'},
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='locationid',
            field=models.UUIDField(default=None, null=True),
        ),
        AppAwareRunPython(
            Backfill('serviceloc', 'locationid', uuid.uuid4),
            reverse_code=AppAwareRunPython.noop,
            hints={'model_name': 'serviceloc'},
        ),
    ]
