# Generated by Django 3.1.7 on 2021-06-07 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0034_auto_20210607_2047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projecttemplate',
            name='slug',
            field=models.CharField(default='', max_length=512),
        ),
    ]
