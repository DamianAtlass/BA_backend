import pytz
from django.core.mail import send_mail
from django.utils import timezone
import os
from datetime import datetime

USER_DATA_DIRECTORY = "userdata"


def convert_to_localtime(utctime, format="%H:%M"):
    utc = utctime.replace(tzinfo=pytz.UTC)
    local_tz = utc.astimezone(timezone.get_current_timezone())
    return local_tz.strftime(format)


def safe_check_dir(folder_array):
    if len(folder_array) == 0:
        print("")
        raise ValueError("Folder_array cannot be empty")

    dir_check = ""
    for folder in folder_array:
        dir_check = os.path.join(dir_check, folder)
        if not os.path.exists(dir_check):
            os.makedirs(dir_check)

    return dir_check


def safe_file_path(file_path):
    """
    Changes file path to the current date, if file already exists.
    Prevents loss of data. Does not write in file or create file.
    :param file_path: relative file path
    :return: old or updated file path
    """
    if os.path.exists(file_path):
        first_part = file_path.split(".")[0]
        file_extension = file_path.split(".")[1]
        date = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        file_path = f"{first_part}_{date}.{file_extension}"

    return file_path

#TODO
def is_testing_user(user):
    if user.userinfo.email == "alice@mail.com" \
            or user.userinfo.email == "ben@mail.com" \
            or user.userinfo.email == "christian@mail.de" \
            or user.userinfo.email == "daniel@mail.de":
        return True
    else:
        return False


def send_confirmation_email(user):

    message = f"Danke für deine Teilnahme an dieser Studie, {user.username}! Gib beim Login diesen Code ein, um dich zu verifizieren: {user.userinfo.verification_code}"

    if is_testing_user(user):
        print("is testing-user, dont send email")
        return 1
    else:
        print("send email!")

    return send_mail(
        subject='Bestätige deine Emailadresse!',
        message=message,
        from_email=None,  # django will use EMAIL_HOST_USER anyway
        recipient_list=[user.userinfo.email],
        fail_silently=False,
    )
