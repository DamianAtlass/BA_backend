from django.db import models
from django.contrib.auth.models import User

# Create your models here.

USER = "USER"


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    alias = models.CharField("Alias", max_length=240, null=True)
    verified = models.BooleanField("Verified", default=False)

    def __str__(self):
        return f"Userinfo for {self.user} ({self.alias})"

    class Meta:
        verbose_name = "UserInfo"
        verbose_name_plural = "UserInfos"


class GraphMessage(models.Model):
    content = models.CharField(max_length=240, null=True)
    author = models.CharField(max_length=25, null=True)
    prev = models.ManyToManyField("self", blank=True)
    next = models.ManyToManyField("self", blank=True)
    is_start = models.BooleanField(null=False, default=False)
    is_end = models.BooleanField(null=False, default=False)

    def __str__(self):
        return f"{self.author}: '{self.content}'"

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class Dialog(models.Model):
    userinfo = models.OneToOneField(UserInfo, related_name="dialog",  on_delete=models.CASCADE, null=True)
    bot_type = models.CharField(max_length=25, null=True)

    def __str__(self):
        return f"Dialog with {self.bot_type}"


class DialogMessage(models.Model):
    #TODO: number field that indecates order
    date = models.DateTimeField(auto_now_add=True)
    dialog = models.ForeignKey(Dialog, related_name="messages", on_delete=models.CASCADE)
    graph_message = models.ForeignKey(GraphMessage, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"[{self.data}]: {self.graph_message.content}"
