# Generated by Django 4.1.5 on 2023-02-25 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_alter_userinfo_completed_dialog'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='verification_code',
            field=models.IntegerField(default=None, null=True, verbose_name='Verification Code'),
        ),
    ]
