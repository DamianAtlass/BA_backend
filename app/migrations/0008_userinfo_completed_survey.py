# Generated by Django 4.1.5 on 2023-02-21 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_remove_userinfo_alias_userinfo_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='completed_survey',
            field=models.BooleanField(default=False, verbose_name='Completed Survey'),
        ),
    ]
