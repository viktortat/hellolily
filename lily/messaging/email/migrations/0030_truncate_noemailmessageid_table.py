# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('email', '0029_emailaccount_only_new'),
    ]

    operations = [
        migrations.RunSQL(
            "TRUNCATE email_noemailmessageid RESTART IDENTITY;",
            "SELECT 1;"  # Although isn't possible, prevent an error on the rollback command.
        ),
    ]
