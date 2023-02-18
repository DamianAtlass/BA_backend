# Generated by Django 4.1.5 on 2023-02-14 20:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dialog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bot_type', models.CharField(max_length=25, null=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dialog', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='userinfo',
            name='last_bot_message_pk',
            field=models.IntegerField(default=-1),
        ),
        migrations.CreateModel(
            name='GraphMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=240, null=True)),
                ('author', models.CharField(max_length=25, null=True)),
                ('is_start', models.BooleanField(default=False)),
                ('is_end', models.BooleanField(default=False)),
                ('next', models.ManyToManyField(blank=True, to='app.graphmessage')),
            ],
        ),
        migrations.CreateModel(
            name='DialogMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField(default=-1)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('dialog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='app.dialog')),
                ('graph_message', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.graphmessage')),
            ],
        ),
    ]