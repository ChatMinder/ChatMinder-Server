# Generated by Django 3.0.8 on 2022-01-05 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_merge_20220105_0920'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='image',
        ),
        migrations.AddField(
            model_name='image',
            name='name',
            field=models.CharField(default='anonymous', max_length=40),
        ),
        migrations.AddField(
            model_name='image',
            name='url',
            field=models.URLField(default='url'),
        ),
    ]
