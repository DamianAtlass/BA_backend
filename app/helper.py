import pytz
from django.utils import timezone
import os
import json
from .models import User
from datetime import datetime



def convert_to_localtime(utctime, format="%H:%M"):
    utc = utctime.replace(tzinfo=pytz.UTC)
    local_tz = utc.astimezone(timezone.get_current_timezone())
    return local_tz.strftime(format)


'''
Saves survey data as json file.
Params:
user_pk: 3 digit pre-zeroed,
data: stringyfied json data'''


def save_survey_data(user_pk, data):
    dir_path = "surveyData"
    file_path = f"{os.path.join(dir_path, user_pk)}.json"
    print("filepath: ", file_path)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # if file exists, add _new (for debugging), there should never be more than 1 file of a participant
    if os.path.exists(file_path):
        first_part = file_path.split(".")[0]
        file_path = f"{first_part}_{convert_to_localtime(datetime.now(), format='%H-%M-%S')}.json"

    print(file_path)
    json_object = json.dumps(data, indent=4)
    print(json_object)
    with open(f"{file_path}", "w") as outfile:
        outfile.write(json_object)

    return os.path.exists(file_path)






