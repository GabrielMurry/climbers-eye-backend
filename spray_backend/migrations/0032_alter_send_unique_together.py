# Generated by Django 4.2.1 on 2023-09-06 16:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('spray_backend', '0031_rename_notes_boulder_description'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='send',
            unique_together=set(),
        ),
    ]
