# Generated by Django 4.2.1 on 2023-09-15 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0008_userprofile_total_pages_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='total_pages_read',
            field=models.IntegerField(default=0),
        ),
    ]
