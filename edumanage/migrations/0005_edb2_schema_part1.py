# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-31 06:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import edumanage.models
import uuid


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
                ('lang', models.CharField(choices=[('en', 'English'), ('el', 'Ελληνικά'), ('hu', 'Magyar')], max_length=5)),
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
            name='instid',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AddField(
            model_name='institution',
            name='stage',
            field=models.PositiveIntegerField(choices=[(0, 'preproduction/test'), (1, 'active')], default=1),
        ),
        migrations.AddField(
            model_name='institutiondetails',
            name='venue_info',
            field=models.CharField(blank=True, db_column='inst_type', max_length=7, validators=[edumanage.models.validate_venue_info]),
        ),
        migrations.AddField(
            model_name='realm',
            name='roid',
            field=models.CharField(db_column='ROid', default='', max_length=255, unique=True),
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
        migrations.AddField(
            model_name='serviceloc',
            name='locationid',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='operation_hours',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='physical_avail',
            field=models.PositiveIntegerField(choices=[(0, 'no restrictions'), (1, 'physical access restrictions')], db_column='availability', default=0),
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
            field=models.CharField(blank=True, db_column='location_type', max_length=7, validators=[edumanage.models.validate_venue_info]),
        ),
        migrations.AddField(
            model_name='serviceloc',
            name='wired_no',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='serviceloc',
            name='AP_no',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
