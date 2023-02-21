# Generated by Django 4.1.5 on 2023-02-21 20:09

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0009_alter_graphmessage_options_alter_history_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinfo',
            name='invited_by',
        ),
        migrations.AddField(
            model_name='userinfo',
            name='invited',
            field=models.ManyToManyField(blank=True, related_name='invited', to=settings.AUTH_USER_MODEL),
        ),
    ]
