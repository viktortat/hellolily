# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenant', '0004_tenant_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='billing_default',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tenant',
            name='timelogging_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
