from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from .helper import convert_to_localtime

# Create your models here.

USER = "USER"


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    email = models.CharField("email", max_length=240, null=True, unique=True)
    verified = models.BooleanField("Verified", default=False)
    last_bot_message_pk = models.IntegerField(default=-1)
    dialog_style = models.CharField("Dialog Style", max_length=60, null=True)
    completed_dialog = models.BooleanField("Completed Dialog", default=False)
    completed_survey = models.BooleanField("Completed Survey", default=False)
    verification_code = models.IntegerField("Verification Code", default=None, null=True, blank=True)
    invited_by = models.ForeignKey(User, related_name="invited", on_delete=models.SET_NULL, null=True, blank=True, default=None)

    def __str__(self):
        return f"[{self.pk}] Userinfo for {self.user} ({self.email})"

    class Meta:
        verbose_name = "UserInfo"
        verbose_name_plural = "UserInfos"


class GraphMessage(models.Model):
    content = models.CharField(max_length=240, null=True)
    author = models.CharField(max_length=25, null=True)
    next = models.ManyToManyField("self", blank=True, symmetrical=False)
    is_start = models.BooleanField(null=False, default=False)
    one_on_one = models.BooleanField(null=True, blank=True, default=None)
    is_end = models.BooleanField(null=False, default=False)

    def __str__(self):
        return f"[{self.pk}] {self.author}: '{self.content}'"

    class Meta:
        verbose_name = "GraphMessage"
        verbose_name_plural = "GraphMessages"


class History(models.Model):
    user = models.OneToOneField(User, related_name="history",  on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.user.username}'s History"

    class Meta:
        verbose_name = "History"
        verbose_name_plural = "Histories"


class HistoryMessage(models.Model):
    order_id = models.IntegerField(null=False, default=-1)
    date = models.DateTimeField(auto_now_add=True)
    history = models.ForeignKey(History, related_name="messages", on_delete=models.CASCADE)
    graph_message = models.ForeignKey(GraphMessage, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"[{self.pk}] ({self.order_id}) {convert_to_localtime(self.date, format='%d.%m. %H:%M:%S')} - {self.graph_message.author}: {self.graph_message.content}"

    class Meta:
        verbose_name = "HistoryMessage"
        verbose_name_plural = "HistoryMessages"


