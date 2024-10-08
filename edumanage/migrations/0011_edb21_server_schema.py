# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-10-19 13:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('edumanage', '0010_auto_bexact_noop'),
    ]

    operations = [
        migrations.CreateModel(
            name='RealmServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_name', models.CharField(help_text='IP address | FQDN hostname', max_length=80)),
                ('server_type', models.PositiveIntegerField(choices=[(0, 'UDP'), (1, 'TLS'), (2, 'F-ticks')], help_text='Realm server type')),
                ('realm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servers', to='edumanage.Realm')),
            ],
            options={
                'verbose_name': 'Realm Server',
                'verbose_name_plural': "Realms' Servers",
            },
        ),
    ]
