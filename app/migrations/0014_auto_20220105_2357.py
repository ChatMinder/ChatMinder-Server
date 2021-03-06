# Generated by Django 3.0.8 on 2022-01-05 23:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_auto_20220105_1001'),
    ]

    operations = [
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('url', models.URLField(blank=True, null=True)),
            ],
            options={
                'db_table': 'link',
            },
        ),
        migrations.AddField(
            model_name='memo',
            name='is_marked',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Bookmark',
        ),
        migrations.AddField(
            model_name='link',
            name='memo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Memo'),
        ),
    ]
