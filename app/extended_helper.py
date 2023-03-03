import os
from datetime import datetime
from django.contrib.auth.models import User

from app.helper import convert_to_localtime
from app.models import UserInfo, GraphMessage, HistoryMessage
import json
import csv


def get_user_score(user=None, weight=1, factor=2):
    invited_users_userinfo = UserInfo.objects.filter(invited_by=user)

    sum = 0
    for _userinfo in invited_users_userinfo:
        if _userinfo.completed_survey:
            sum += get_user_score(user=_userinfo.user, weight=weight/factor, factor=factor)
    return sum + weight


def get_bot_messages(bot_response: GraphMessage, user: User):
    bot_responses = []
    while True:
        # history_message in history
        new_history_message = HistoryMessage(order_id=len(user.history.messages.all()) + 1,
                                             history=user.history,
                                             graph_message=bot_response)
        new_history_message.save()
        bot_responses.append({"author": bot_response.author,
                              "content": bot_response.content,
                              "date": datetime.now().strftime("%H:%M"),
                              "dialogIsComplete": bot_response.is_end})

        # remember point in conversation
        user.userinfo.last_bot_message_pk = bot_response.pk
        user.userinfo.save()

        # if not last node and next != usernode
        if bot_response.is_end:
            print("DIALOG FINISHED")
            user.userinfo.completed_dialog = True
            user.userinfo.save()
            result = write_messages(user)
            print("Write messages:", result)
            return bot_response, bot_responses
        else:
            if bot_response.next.all()[0].author == "USER":
                return bot_response, bot_responses
            else:
                bot_response = bot_response.next.all()[0]


def write_messages(user=None):
    dir_path = "log"
    file_path = f"{os.path.join(dir_path, f'{user.pk:03}')}.txt"
    print("filepath: ", file_path)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    print(file_path)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        header = ['date', 'author', "content", "order_id", "pk"]
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for message in user.history.messages.all():
            writer.writerow([convert_to_localtime(message.date, "%d/%m/%Y_%H:%M:%S"),
                             message.graph_message.author,
                             message.graph_message.content,
                             message.order_id,
                             message.graph_message.pk]
            )

    return os.path.exists(file_path)
