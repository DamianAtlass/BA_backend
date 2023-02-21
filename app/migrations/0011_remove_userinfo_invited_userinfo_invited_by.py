# Generated by Django 4.1.5 on 2023-02-21 20:22

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0010_remove_userinfo_invited_by_userinfo_invited'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userinfo',
            name='invited',
        ),
        migrations.AddField(
            model_name='userinfo',
            name='invited_by',
            field=models.ManyToManyField(blank=True, related_name='invited_by', to=settings.AUTH_USER_MODEL),
        ),
    ]