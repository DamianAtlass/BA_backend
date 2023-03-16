import os
from datetime import datetime
from django.contrib.auth.models import User

from app.helper import convert_to_localtime, safe_check_dir, safe_file_path, USER_DATA_DIRECTORY
from app.models import UserInfo, GraphMessage, HistoryMessage
import json
import csv

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
            result = log_messages(user)
            print("Write messages:", result)
            return bot_response, bot_responses
        else:
            if bot_response.next.all()[0].author == "USER":
                return bot_response, bot_responses
            else:
                bot_response = bot_response.next.all()[0]


def log_messages(user=None):
    dir_path = safe_check_dir([USER_DATA_DIRECTORY, "log"])
    file_path = f"{os.path.join(dir_path, f'{user.pk:03}')}.csv"
    file_path = safe_file_path(file_path)
    print("filepath: ", file_path)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    print(file_path)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        header = ['date', 'author', "content", "order_id", "pk"]
        #TODO set quote char to quotechar='\'' when live
        writer = csv.writer(csvfile, delimiter=',', quotechar='\"')
        writer.writerow(header)
        for message in user.history.messages.all():
            writer.writerow([convert_to_localtime(message.date, "%d-%m-%Y_%H-%M-%S"),
                             message.graph_message.author,
                             message.graph_message.content,
                             message.order_id,
                             message.graph_message.pk]
                            )

    return os.path.exists(file_path)


def allowed_to_display(user=None, choice=None, parent=None):
    """
    :param user:
    :param choice: GraphMessage with author="USER"
    :param parent: GraphMessage of bot which points to choice
    :return:
    """

    if choice.author !="USER":
        print("ERROR")

    # get sibling pks relative to choice
    siblings_pk = list(map(lambda o: o.pk, parent.next.all()))
    print("siblings_pk:", siblings_pk)

    history_messages = user.history.messages.all()
    unique_graph_messages_pks_from_history = set(map(lambda x: x.graph_message.pk, history_messages))
    print("unique_graph_messages_pks_from_history:", unique_graph_messages_pks_from_history)

    print("choice.pk:", choice.pk)
    if choice.pk in unique_graph_messages_pks_from_history:
        print(f"path {choice.content} already taken")
        return False

    if choice.explore_siblings == 0:
        print("Result: explore_siblings == 0", True)
        return True

    explored_path = 0
    for unique_graph_messages_pk in unique_graph_messages_pks_from_history:
        if unique_graph_messages_pk in siblings_pk:
            explored_path += 1

    result = True if explored_path >= choice.explore_siblings else False

    print("Result: ", result)
    return result
