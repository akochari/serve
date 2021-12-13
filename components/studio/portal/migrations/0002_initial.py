# Generated by Django 4.0 on 2021-12-13 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('models', '0002_initial'),
        ('portal', '0001_initial'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='publishedmodel',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project'),
        ),
        migrations.AddField(
            model_name='publicmodelobject',
            name='model',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='models.model'),
        ),
    ]
