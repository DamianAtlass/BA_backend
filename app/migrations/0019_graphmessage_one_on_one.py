# Generated by Django 4.1.5 on 2023-03-06 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_remove_history_bot_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='graphmessage',
            name='one_on_one',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
