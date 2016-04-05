# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Citation',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('citation_number', models.IntegerField(default=0, null=True, blank=True)),
                ('citation_date', models.DateTimeField(null=True, blank=True)),
                ('first_name', models.CharField(default=b'', max_length=255)),
                ('last_name', models.CharField(default=b'', max_length=255)),
                ('last_name_phone', models.CharField(default=b'', max_length=255)),
                ('date_of_birth', models.DateTimeField(null=True, blank=True)),
                ('defendant_address', models.CharField(default=b'', max_length=255)),
                ('defendant_city', models.CharField(default=b'', max_length=255)),
                ('defendant_state', models.CharField(default=b'', max_length=255)),
                ('drivers_license_number', models.CharField(default=b'', max_length=255)),
                ('drivers_license_number_phone', models.CharField(default=b'', max_length=255)),
                ('court_date', models.DateTimeField(null=True, blank=True)),
                ('court_location', models.CharField(default=b'', max_length=255)),
                ('court_address', models.CharField(default=b'', max_length=255)),
            ],
            options={
                'verbose_name': 'Citation',
                'verbose_name_plural': 'Citations',
            },
        ),
        migrations.CreateModel(
            name='Violation',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('citation_number', models.IntegerField(default=0, null=True, blank=True)),
                ('violation_number', models.CharField(default=b'', max_length=255)),
                ('violation_description', models.CharField(default=b'', max_length=255)),
                ('warrant_status', models.BooleanField(default=False)),
                ('warrant_number', models.CharField(default=b'', max_length=255)),
                ('status', models.CharField(default=b'', max_length=255)),
                ('status_date', models.DateTimeField(null=True, blank=True)),
                ('fine_amount', models.CharField(default=b'', max_length=255)),
                ('court_cost', models.CharField(default=b'', max_length=255)),
            ],
            options={
                'verbose_name': 'Violation',
                'verbose_name_plural': 'Violations',
            },
        ),
        migrations.DeleteModel(
            name='Fish',
        ),
    ]
