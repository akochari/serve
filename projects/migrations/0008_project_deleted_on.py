# Generated by Django 5.1.1 on 2024-10-17 07:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0007_alter_flavor_ephmem_lim"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="deleted_on",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
