# Generated by Django 3.0.2 on 2020-01-19 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_auto_20200119_0918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='twFile',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
