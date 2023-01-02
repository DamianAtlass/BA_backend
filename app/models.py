from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    alias = models.CharField("Alias", max_length=240, null=True)
    verified = models.BooleanField("Verified", default=False)

    def __str__(self):
        return f"Userinfo for {self.user} ({self.alias})"

    class Meta:
        verbose_name = "UserInfo"
        verbose_name_plural = "UserInfos"
