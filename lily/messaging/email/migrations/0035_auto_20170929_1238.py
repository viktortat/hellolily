# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-29 12:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0034_auto_20170929_1237'),
    ]

    operations = [
        migrations.RenameField(
            model_name='emailoutboxmessage',
            old_name='original_attachment_ids_char',
            new_name='original_attachment_ids',
        ),
        migrations.RenameField(
            model_name='emailoutboxmessage',
            old_name='template_attachment_ids_char',
            new_name='template_attachment_ids',
        ),
    ]
