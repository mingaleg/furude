# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-07 10:28
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('secure_proxy', '0002_auto_20171107_0758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cacher',
            name='content',
            field=models.FileField(blank=True, editable=False, null=True, upload_to='cache_dir'),
        ),
        migrations.AlterField(
            model_name='cacher',
            name='last_updated',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='cacher',
            name='status',
            field=models.CharField(default='OK', editable=False, max_length=2),
        ),
        migrations.AlterField(
            model_name='cacher',
            name='status_comment',
            field=models.TextField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='cacher',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
