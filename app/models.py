from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from .helper import convert_to_localtime

# Create your models here.

USER = "USER"


class UserInfo(models.Model):
    user = models.OneToOneField(User, related_name="userinfo",  on_delete=models.CASCADE, null=True)
    email = models.CharField("email", max_length=240, null=True, unique=True)
    rushed = models.BooleanField("Rushed (through interaction)", default=False)
    last_bot_message_pk = models.IntegerField(default=-1)
    dialog_style = models.CharField("Dialog Style", max_length=60, null=True)
    completed_dialog = models.BooleanField("Completed Dialog", default=False)
    completed_survey_part1 = models.BooleanField("Survey Part 1", default=False)
    completed_survey_part2 = models.BooleanField("Survey Part 2", default=False)
    verification_code = models.IntegerField("Verification Code", default=None, null=True, blank=True)
    invited_by = models.ForeignKey(User, related_name="invited", on_delete=models.SET_NULL, null=True, blank=True, default=None)

    def __str__(self):
        return f"[{self.pk}] Userinfo for {self.user} ({self.email})"

    def get_user_score(self, weight=1, factor=2):
        if self.rushed:
            return 1  # give the user a point even if he's rushed to keep his motivation up.
            # notice that he doesn't get a point when it's calculated recursively
        else:
            return self.get_user_score_rec(weight, factor)

    def get_user_score_rec(self, weight=1, factor=2):
        if not self.completed_survey_part2:
            return 0

        user = self.user
        userinfo_group = UserInfo.objects.filter(invited_by=user)

        sum = 0
        for _userinfo in userinfo_group:
            sum += _userinfo.get_user_score(weight=weight/factor, factor=factor)

        if self.rushed:
            return sum
        return sum + weight

    def get_directly_invited_len(self):
        return len(UserInfo.objects.filter(invited_by=self.user))

    def get_total_invited_len(self):
        return self.total_invited_len_rec() - 1

    def total_invited_len_rec(self):
        user = self.user
        print(" invited ", user.username)
        userinfo_group = UserInfo.objects.filter(invited_by=user)

        sum = 0
        for _userinfo in userinfo_group:
            sum += _userinfo.total_invited_len_rec()
        if self.rushed:
            return sum
        return sum + 1

    def get_directly_recruited_len(self):
        return len(UserInfo.objects.filter(invited_by=self.user, completed_survey_part2=True, rushed=False))

    def get_total_recruited_len(self):
        if self.rushed:
            return 0
        return self.total_recruited_len_rec() - 1

    #basically the same as get_user_score, just without weights and factor. didn't want to reuse for simplicity
    def total_recruited_len_rec(self):
        if not self.completed_survey_part2:
            return 0

        user = self.user
        userinfo_group = UserInfo.objects.filter(invited_by=user, completed_survey_part2=True, rushed=False)

        sum = 0
        for _userinfo in userinfo_group:
            sum += _userinfo.total_recruited_len_rec()

        if self.rushed:
            return sum
        return sum + 1

    class Meta:
        verbose_name = "UserInfo"
        verbose_name_plural = "UserInfos"


class GraphMessage(models.Model):
    content = models.CharField(max_length=500, null=True)
    author = models.CharField(max_length=25, null=True)
    next = models.ManyToManyField("self", blank=True, symmetrical=False)
    is_start = models.BooleanField(null=False, default=False)
    one_on_one = models.BooleanField(null=True, blank=True, default=None)
    is_end = models.BooleanField(null=False, default=False)
    explore_siblings = models.IntegerField("Min explored sibling paths", default=0, null=True, blank=True)

    def __str__(self):
        return f"[{self.pk:03}] -> {self.get_next_pks()} {self.author}: '{self.content}'"

    def get_next_pks(self):
        list = []
        for gm in self.next.all():
            list.append(gm.pk)
        return list
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


