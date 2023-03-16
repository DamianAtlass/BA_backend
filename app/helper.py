import pytz
from django.core.mail import send_mail
from django.utils import timezone
import os
import json
from datetime import datetime

USER_DATA_DIRECTORY = "userdata"


def convert_to_localtime(utctime, format="%H:%M"):
    utc = utctime.replace(tzinfo=pytz.UTC)
    local_tz = utc.astimezone(timezone.get_current_timezone())
    return local_tz.strftime(format)


def safe_check_dir(folder_array):
    if len(folder_array) == 0:
        print("")
        raise ValueError("folder_array cannot be empty")

    dir_check = ""
    for folder in folder_array:
        dir_check = os.path.join(dir_check, folder)
        if not os.path.exists(dir_check):
            os.makedirs(dir_check)

    return dir_check


def safe_file_path(file_path):
    """
    Changes file path to the current date, if file already exists. Prevents loss of data.
    :param file_path: relative file path
    :return: old or updated file path
    """
    if os.path.exists(file_path):
        first_part = file_path.split(".")[0]
        file_extension = file_path.split(".")[1]
        date = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        file_path = f"{first_part}_{date}.{file_extension}"

    return file_path



def save_survey_data(user_pk, survey_part, data):
    """
    Saves survey data as json file.

    :param user_pk: 3 digit pre-zeroed
    :param survey_part: part of survey (1 or 2)
    :param data: stringyfied json data
    :return: true if file created else false
    """

    dir_path = safe_check_dir([USER_DATA_DIRECTORY, f"surveyData_part{survey_part}"])
    file_path = f"{os.path.join(dir_path, user_pk)}.json"



    # TODO take out if live???
    # if file exists, add _new (for debugging), there should never be more than 1 file of a participant
    file_path = safe_file_path(file_path)

    print(file_path)
    json_object = json.dumps(data, indent=4)
    print(json_object)
    with open(file_path, "w", encoding='utf-8') as outfile:
        outfile.write(json_object)

    return os.path.exists(file_path)


def is_testing_user(user):
    if user.userinfo.email == "alice@mail.com" \
            or user.userinfo.email == "ben@mail.com" \
            or user.userinfo.email == "christian@mail.de" \
            or user.userinfo.email == "daniel@mail.de":
        return True
    else:
        return False


def send_confirmation_email(user):
    print("send email")

    message = f"Danke für deine Teilnahme an dieser Studie, {user.username}! Gib beim Login diesen Code ein, um dich zu verifizieren: {user.userinfo.verification_code}"

    if is_testing_user(user):
        return 1

    return send_mail(
        subject='Bestätige deine Emailadresse!',
        message=message,
        from_email=None,  # django will use EMAIL_HOST_USER anyway
        recipient_list=[user.userinfo.email],
        fail_silently=False,
    )
