# Generated by Django 3.0.8 on 2022-01-04 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20220104_0217'),
    ]

    operations = [
        migrations.AddField(
            model_name='memo',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='%Y/%m/%d'),
        ),
        migrations.DeleteModel(
            name='Link',
        ),
    ]
