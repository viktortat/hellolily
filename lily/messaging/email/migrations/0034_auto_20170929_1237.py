# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-29 12:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0033_auto_20170929_1222'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailoutboxmessage',
            name='original_attachment_ids',
        ),
        migrations.RemoveField(
            model_name='emailoutboxmessage',
            name='template_attachment_ids',
        ),
    ]
