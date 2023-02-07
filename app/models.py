from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

USER = "USER"


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    alias = models.CharField("Alias", max_length=240, null=True)
    verified = models.BooleanField("Verified", default=False)

    def __str__(self):
        return f"[{self.pk}] Userinfo for {self.user} ({self.alias})"

    class Meta:
        verbose_name = "UserInfo"
        verbose_name_plural = "UserInfos"


class GraphMessage(models.Model):
    content = models.CharField(max_length=240, null=True)
    author = models.CharField(max_length=25, null=True)
    next = models.ManyToManyField("self", blank=True, symmetrical=False)
    is_start = models.BooleanField(null=False, default=False)
    is_end = models.BooleanField(null=False, default=False)

    def __str__(self):
        return f"[{self.pk}] {self.author}: '{self.content}'"


class Dialog(models.Model):
    user = models.OneToOneField(User, related_name="dialog",  on_delete=models.CASCADE, null=True)
    bot_type = models.CharField(max_length=25, null=True)

    def __str__(self):
        return f"Dialog between {self.bot_type} and {self.user.username}"


class DialogMessage(models.Model):
    order_id = models.IntegerField(null=False, default=-1)
    date = models.DateTimeField(auto_now_add=True)
    dialog = models.ForeignKey(Dialog, related_name="messages", on_delete=models.CASCADE)
    graph_message = models.ForeignKey(GraphMessage, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"[{self.pk}] ({self.order_id}) {self.date.strftime('%Y-%m-%d %H:%M:%S')} - {self.graph_message.author}: {self.graph_message.content}"
