# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenant', '0004_tenant_currency'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gfk_object_id', models.PositiveIntegerField()),
                ('hours_logged', models.DecimalField(max_digits=7, decimal_places=3)),
                ('billable', models.BooleanField(default=False)),
                ('date', models.DateTimeField()),
                ('gfk_content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('tenant', models.ForeignKey(to='tenant.Tenant', blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('case', models.ForeignKey(blank=True, to='cases.Case', null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
