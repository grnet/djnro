# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edumanage', '0002_chg_field_instserver_instid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='institutiondetails',
            name='oper_name',
            field=models.CharField(help_text='The primary, registered domain name for your institution, eg. example.com.<br>This is used to derive the Operator-Name attribute according to RFC5580, par.4.1, using the REALM namespace.', max_length=252, null=True, blank=True),
        ),
    ]
