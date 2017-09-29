# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-09-19 15:47
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0031_auto_20170801_0900'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailoutboxmessage',
            name='original_attachment_ids_char',
            field=models.CharField(default=b'', max_length=255, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')]),
        ),
        migrations.AddField(
            model_name='emailoutboxmessage',
            name='template_attachment_ids_char',
            field=models.CharField(default=b'', max_length=255, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')]),
        ),
    ]