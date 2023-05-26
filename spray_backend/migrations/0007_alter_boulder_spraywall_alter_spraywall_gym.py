# Generated by Django 4.2.1 on 2023-05-22 19:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('spray_backend', '0006_boulder_description_boulder_first_ascent_person_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boulder',
            name='spraywall',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='spray_backend.spraywall'),
        ),
        migrations.AlterField(
            model_name='spraywall',
            name='gym',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='spray_backend.gym'),
        ),
    ]