from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    alias = models.CharField("alias", max_length=240)
    verified = models.BooleanField("Verified", default=False)




