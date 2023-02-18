# Generated by Django 4.1.5 on 2023-02-14 20:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0004_rename_dialogmessage_historymessage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historymessage',
            old_name='dialog',
            new_name='history',
        ),
        migrations.AlterField(
            model_name='history',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='history', to=settings.AUTH_USER_MODEL),
        ),
    ]