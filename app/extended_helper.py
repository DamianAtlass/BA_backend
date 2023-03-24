import os
import random
from datetime import datetime
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.core.mail import send_mail
from app.helper import convert_to_localtime, safe_check_dir, safe_file_path, USER_DATA_DIRECTORY, get_link_to_website, \
    create_invitation_link
from app.models import UserInfo, GraphMessage, HistoryMessage
import json
import csv

#TODO set this to an appropriate amount
MINIMUM_DURATION_MINUTES = 3.5

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
            print(f"DIALOG FINISHED FOR {user.username}")
            user.userinfo.completed_dialog = True
            user.userinfo.rushed = check_if_rushed(user)
            user.userinfo.save()

            log_messages(user)
            return bot_response, bot_responses
        else:
            if bot_response.next.all()[0].author == "USER":
                return bot_response, bot_responses
            else:
                bot_response = bot_response.next.all()[0]


def log_messages(user=None):
    dir_path = safe_check_dir([USER_DATA_DIRECTORY, "log"])
    if user.userinfo.rushed:
        suffix = "_rushed"
    else:
        suffix = ""
    file_path = f"{os.path.join(dir_path, f'{user.pk:03}{suffix}')}.csv"
    file_path = safe_file_path(file_path)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        header = ['date', 'author', "content", "order_id", "pk"]
        writer = csv.writer(csvfile, delimiter=',', quotechar='\'')
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

    # get sibling pks relative to choice
    siblings_pk = list(map(lambda o: o.pk, parent.next.all()))

    history_messages = user.history.messages.all()
    unique_graph_messages_pks_from_history = set(map(lambda x: x.graph_message.pk, history_messages))


    if choice.pk in unique_graph_messages_pks_from_history:
        return False

    if choice.explore_siblings == 0:
        return True

    explored_path = 0
    for unique_graph_messages_pk in unique_graph_messages_pks_from_history:
        if unique_graph_messages_pk in siblings_pk:
            explored_path += 1

    result = True if explored_path >= choice.explore_siblings else False

    return result


def create_new_verification_code(user):
    while True:
        new_code = random.randint(100000, 999999)
        if not (user.userinfo.verification_code == new_code):
            break
    user.userinfo.verification_code = new_code
    user.userinfo.save()



def get_interaction_duration_minutes(user):
    msg_len = len(user.history.messages.all())
    if msg_len == 0:
        return 0

    first_message_date = user.history.messages.all()[0].date
    last_message_date = user.history.messages.all()[msg_len-1].date

    return (last_message_date - first_message_date).total_seconds()/60

def check_if_rushed(user):
    difference_minutes = get_interaction_duration_minutes(user)

    if difference_minutes < MINIMUM_DURATION_MINUTES:
        return True
    else:
        return False


def verify_token(request_token, username, return_response_on_success=False):
    try:
        user = User.objects.get(username=username)

        token, created = Token.objects.get_or_create(user=user)
        if token.key == request_token:
            if return_response_on_success:
                return Response(status=status.HTTP_200_OK)
            else:
                return None
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error": "UNAUTHORIZED"
                            })

    except User.DoesNotExist as e:
        return Response(status=status.HTTP_404_NOT_FOUND,
                        data={
                            "error": "USER_NOT_FOUND"
                        })


def save_survey_data(user_pk, survey_part, data):
    """
    Saves survey data as json file.

    :param user_pk: 3 digit pre-zeroed
    :param survey_part: part of survey (1 or 2)
    :param data: stringyfied json data
    :return: true if file created else false
    """

    if User.objects.get(pk=user_pk).userinfo.rushed:
        suffix = "_rushed"
    else:
        suffix = ""

    dir_path = safe_check_dir([USER_DATA_DIRECTORY, f"surveyData_part{survey_part}"])
    file_path = f"{os.path.join(dir_path, f'{user_pk}{suffix}')}.json"



    # if file exists, add _new (for debugging), there should never be more than 1 file of a participant
    file_path = safe_file_path(file_path)

    json_object = json.dumps(data, indent=4)
    with open(file_path, "w", encoding='utf-8') as outfile:
        outfile.write(json_object)

    return os.path.exists(file_path)


def send_reminder_email(reminder_type):
    """
    :param reminder_type:
    :return:
    int email_total: number of total emails that were tried to send
    int email_success: number of sucessfully emails
    """
    count_total = 0
    count_success = 0

    for user in User.objects.all():

        if user.is_staff \
                or (reminder_type == "completed" and not user.userinfo.completed_survey_part2) \
                or (reminder_type == "not_completed" and user.userinfo.completed_survey_part2):
            continue

        count_total += 1

        if reminder_type == "completed":
            subject = "Vielen Dank für deine Teilnahme! Das ist dein Score..."

            message = f"""Danke, dass du an der Studie teilgenommen hast, {user.username}!\n
            Hier ist dein Score:\n
            Donuts🍩: {user.userinfo.get_total_recruited_len()}
            Cookies🍪: {user.userinfo.get_user_score()}
            \n\n
            Nicht schlecht, aber denke daran, dass du deine Chancen zu gewinnen immer noch steigern kannst!\n
            Teile dazu einfach diesen Link mit deinen Freunden: {create_invitation_link(user.pk)}
            """
        else:
            subject = "Du bist noch nicht fertig!"

            message = f"""Danke, für dein Interesse an der Studie, {user.username}!\n
            Noch bist du aber nicht fertig, hier zurück zur Studie: {get_link_to_website()}\n
            """

        result = send_mail(
            subject=subject,
            message=message,
            from_email=None,  # django will use EMAIL_HOST_USER anyway
            recipient_list=[user.userinfo.email],
            fail_silently=False,
        )

        if result == 1:
            print(f"SENT REMINDER MAIL TO {user.username}")
            count_success += 1

    return count_total, count_success
