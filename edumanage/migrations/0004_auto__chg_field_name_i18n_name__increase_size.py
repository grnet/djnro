# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edumanage', '0003_auto__chg_field_institutiondetails_oper_name__increase_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='name_i18n',
            name='name',
            field=models.CharField(max_length=255),
        ),
    ]
