# Generated by Django 4.2.1 on 2023-06-05 16:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('spray_backend', '0012_send_attempts_send_grade_send_notes_send_quality'),
    ]

    operations = [
        migrations.CreateModel(
            name='Circuit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('boulders', models.ManyToManyField(related_name='circuits', to='spray_backend.boulder')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spray_backend.person')),
                ('spraywall', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='spray_backend.spraywall')),
            ],
        ),
    ]