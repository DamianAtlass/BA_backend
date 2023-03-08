from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from env import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
from rest_framework.authtoken.models import Token

from .extended_helper import get_bot_messages
from .helper import convert_to_localtime, save_survey_data, send_confirmation_email
from .models import UserInfo, History, GraphMessage, HistoryMessage
from django.contrib.auth import authenticate, login as django_login
import random

# dialog styles
DIALOG_STYLE_ONE_ON_ONE = "ONE_ON_ONE"
DIALOG_STYLE_COLORED_BUBBLES = "COLORED_BUBBLES"
DIALOG_STYLE_CLASSIC_GROUP = "CLASSIC_GROUP"
DIALOG_STYLE_PICTURE = "PROFILE_PICTURES"

DEFAULT_PASSWORD = "DEFAULT_PASSWORD"

USERSCORE_MULTIPLIER = 100


@api_view(['GET', 'POST', 'DELETE'])
def ok(request):
    if request.method == 'GET':
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'POST':
        for user in User.objects.all():
            print(f"User {user.username}: {user.pk}")
        print(request.data)
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'DELETE':
        User.objects.create_user(username="admin", password=DEFAULT_PASSWORD)

        return Response(status=status.HTTP_200_OK, data={"message": "OK"})


@api_view(['GET'])
def createadmin(request):
    superuser = User.objects.create_superuser(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
    superuser.save()
    print("Created admin")
    token, created = Token.objects.get_or_create(user=superuser)
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def login(request):
    print("LOGIN ATTEMPT")
    if request.method == 'POST':
        print(request.data)
        username = request.data.get("username")

        try:
            User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={
                                "error-message": "Dieser Nutzer ist nicht in der Datenbank.",
                                "error": "USER_NOT_FOUND",
                            })

        authenticated_user = authenticate(request, username=username, password=DEFAULT_PASSWORD)

        if authenticated_user is not None:
            django_login(request, authenticated_user)
            data = {
                "success": "LOGIN_SUCCESS",
                "dialog_style": authenticated_user.userinfo.dialog_style,
                "username": authenticated_user.username,
                "user_pk": authenticated_user.pk,
                "completed_dialog": authenticated_user.userinfo.completed_dialog,
                "completed_survey_part1": authenticated_user.userinfo.completed_survey_part1,
                "completed_survey_part2": authenticated_user.userinfo.completed_survey_part2,
            }
            print("data: ", data)

            if authenticated_user.userinfo.verified:
                return Response(status=status.HTTP_200_OK, data=data)
            else:
                verification_code = request.data.get("verification_code")
                if verification_code:
                    verification_code = int(verification_code)
                    if verification_code == authenticated_user.userinfo.verification_code:
                        authenticated_user.userinfo.verified = True
                        authenticated_user.userinfo.save()
                        data = {
                            "success": "LOGIN_SUCCESS",
                            "dialog_style": authenticated_user.userinfo.dialog_style,
                            "username": authenticated_user.username,
                            "user_pk": authenticated_user.pk,
                            "completed_dialog": authenticated_user.userinfo.completed_dialog,
                            "completed_survey_part1": authenticated_user.userinfo.completed_survey_part1,
                            "completed_survey_part2": authenticated_user.userinfo.completed_survey_part2,
                        }
                        print("data: ", data)
                        return Response(status=status.HTTP_200_OK, data=data)
                    else:
                        return Response(status=status.HTTP_401_UNAUTHORIZED,
                                        data={
                                            "error-message": "Falscher Verifizierungscode.",
                                            "error": "WRONG_VERIFICATION_CODE"
                                        })

                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED,
                                    data={
                                        "error-message": "Bitte gib den Verifizierungscode an, der an deine Emailadresse geschickt wurde. Sieh ggf. im Spam-Ordner nach.",
                                        "error": "VERIFICATION_NECESSARY"
                                    })
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error-message": "Falsche Anmeldeinformationen.",
                                "error": "WRONG_CREDENTIALS"
                            })


@api_view(['POST'])
def adminlogin(request):
    print("ADMIN LOGIN ATTEMPT")
    if request.method == 'POST':
        print(request.data)
        username = request.data.get("username")
        password = request.data.get("admin_password")

        try:
            User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={
                                "error-message": "Dieser Nutzer ist nicht in der Datenbank.",
                                "error": "USER_NOT_FOUND",
                            })

        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is not None:
            django_login(request, authenticated_user)

            token, created = Token.objects.get_or_create(user=authenticated_user)

            return Response(status=status.HTTP_200_OK, data={
                "success": "LOGIN_SUCCESS",
                "username": authenticated_user.username,
                "token": token.key
            })

        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error-message": "Falsche Admin-Anmeldeinformationen.",
                                "error": "WRONG_CREDENTIALS"
                            })


@api_view(['POST'])
def getuserdata(request):
    if request.method == 'POST':
        admin = User.objects.get(username=ADMIN_USERNAME)

        token, created = Token.objects.get_or_create(user=admin)

        if not token.key == request.data.get("token", None):
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={
                "error-message": "wrong token"
            })

        all_userinfos = []

        for user in User.objects.all():
            if user.is_staff:
                continue

            directly_invited_len = len(UserInfo.objects.filter(invited_by=user))

            print("total inv", user.username)
            total_invited_len = user.userinfo.get_total_invited_len()

            directly_recruited_len = user.userinfo.get_directly_recruited_len()
            total_recruited_len = user.userinfo.get_directly_recruited_len()

            all_userinfos.append(
                {
                    "username": user.username,
                    "email": user.userinfo.email,
                    "verified": user.userinfo.verified,
                    "dialog_style": user.userinfo.dialog_style,
                    "completed_dialog": user.userinfo.completed_dialog,
                    "completed_survey_part1": user.userinfo.completed_survey_part1,
                    "completed_survey_part2": user.userinfo.completed_survey_part2,
                    "user_pk": user.pk,
                    "invited_by": user.userinfo.invited_by.username if user.userinfo.invited_by else "",
                    "user_score": user.userinfo.get_user_score() * USERSCORE_MULTIPLIER,
                    "directly_invited_len": directly_invited_len,
                    "total_invited_len": total_invited_len,
                    "directly_recruited_len": directly_recruited_len,
                    "total_recruited_len": total_recruited_len,
                }
            )

        return Response(status=status.HTTP_200_OK, data={"all_userinfos": all_userinfos})


@api_view(['GET', 'POST', 'DELETE'])
def accounts(request):
    if request.method == 'POST':
        print(request.data)

        ###check if email exists in userinfo before actuall user is created

        try:
            UserInfo.objects.get(email=request.data.get("email"))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={"error": "EMAIL_NOT_UNIQUE",
                                  "error-message": "Emailadresse bereits in Benutzung!"})
        except UserInfo.DoesNotExist as e:
            pass

        ### create user
        try:
            new_user = User.objects.create_user(username=request.data.get("username"),
                                                password=DEFAULT_PASSWORD)
            new_user.save()
            print(f"User {new_user.username} created!")

        except IntegrityError as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={"error": str(e),
                                  "error-message": "Benutzername ungültig oder bereits vergeben!"})

        ### create userinfo
        # TODO: remove partly(!) when live
        match request.data.get("email"):
            case "alice@mail.com":
                dialog_style = DIALOG_STYLE_ONE_ON_ONE
            case "ben@mail.com":
                dialog_style = DIALOG_STYLE_COLORED_BUBBLES
            case "christian@mail.de":
                dialog_style = DIALOG_STYLE_CLASSIC_GROUP
            case "daniel@mail.de":
                dialog_style = DIALOG_STYLE_PICTURE
            case _:
                dialog_style = random.choice([DIALOG_STYLE_ONE_ON_ONE, DIALOG_STYLE_COLORED_BUBBLES,
                                              DIALOG_STYLE_CLASSIC_GROUP, DIALOG_STYLE_PICTURE])

        userinfo = UserInfo(user=new_user,
                            email=request.data.get("email"),
                            dialog_style=dialog_style,
                            verification_code=random.randint(100000, 999999))
        userinfo.save()

        ### create history
        new_history = History(user=new_user)
        new_history.save()

        ### set invited by
        if request.data.get("invitedBy"):
            try:
                inviting_user = User.objects.get(username=request.data.get("invitedBy"))

                if not inviting_user.userinfo.completed_survey_part2:
                    return Response(status=status.HTTP_400_BAD_REQUEST,
                                    data={"error": "Einladender Nutzer muss Studie vorher ausfüllen!"})

                new_user.userinfo.invited_by = inviting_user
                new_user.userinfo.save()
            except User.DoesNotExist as e:
                print("Error:", e, "Einladender Nutzer existiert nicht!")

        # try to send verification email
        try:
            result = send_confirmation_email(new_user)

            # sending process was not successfull
            if not result == 1:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                data={"error": "Senden der Email fehlgeschlagen!"})

        # TODO specify if an exception ever occurs
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

        return Response(status=status.HTTP_201_CREATED,
                        data={"success-message": (
                            f"Account erstellt! Eine Email wurde an {new_user.userinfo.email} gesendet. "
                            "Du kannst dieses Popup nun schließen.")})

    if request.method == 'DELETE':
        print(request.data)
        username = request.data.get("username", None)
        tmp = username
        try:
            User.objects.get(username=username).delete()
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={
                                "error": str(e)
                            })
        else:
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                print(f"User {tmp} was successfully deleted!")
                return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def invite(request, user_pk=""):
    if request.method == 'GET':
        print("enter function")
        user_pk = int(user_pk)

        try:
            inviting_user = User.objects.get(pk=user_pk)
            return Response(status=status.HTTP_200_OK, data={"inviting_user": inviting_user.username})
        except User.DoesNotExist as e:
            print("didnt found user")
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={"error": str(e),
                                  "error-message": "Einladender Nutzer existiert nicht! Link ist kaputt!"})


@api_view(['GET'])
def inv(request, user_pk=""):
    if request.method == 'GET':
        user_pk = int(user_pk)
        user = User.objects.get(pk=user_pk)
        directly_recruited_len = user.userinfo.get_directly_recruited_len()
        # m = map(lambda x: x.user.username, invited_users)
        # map(lambda x: print(x), m)

        user_score = user.userinfo.get_user_score() * USERSCORE_MULTIPLIER

        return Response(status=status.HTTP_200_OK, data={
            "directly_recruited_len": directly_recruited_len,
            "user_score": user_score})


@api_view(['DELETE'])
def history(request):
    if request.method == 'DELETE':
        username = request.data.get("username", None)
        user = User.objects.get(username=username)

        print("Delete history of ", username)

        user.userinfo.last_bot_message_pk = -1
        user.userinfo.completed_survey_part1 = False
        user.userinfo.completed_survey_part2 = False
        user.userinfo.completed_dialog = False
        user.userinfo.save()

        try:
            user.history.delete()
        except History.DoesNotExist as e:
            print(e)
            pass
        else:
            print(f"History of {username} was successfully deleted!")
        new_history = History(user=User.objects.get(username=username))
        new_history.save()

        return Response(status=status.HTTP_200_OK)


@api_view(['POST', 'DELETE'])
def survey_data(request, user_pk="", survey_part=""):
    if request.method == 'POST':
        survey_part = int(survey_part)
        if not (survey_part == 1 or survey_part == 2):
            return Response(status=status.HTTP_404_NOT_FOUND, data={
                "error": "NO_SUCH_SURVEY",
                "error-message": f"You tried to hand in survey No {survey_part}, but that doesn't exist!"})

        # check if user exists & if data has already been sent
        try:
            user = User.objects.get(pk=int(user_pk))
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})

        # distinguish between survey part 1 and 2
        if survey_part == 1:
            #check if handed in aleady
            if user.userinfo.completed_survey_part1:
                return Response(status=status.HTTP_403_FORBIDDEN, data={
                    "error": "HANDED_IN_ALREADY",
                    "error-message": f"You handed survey {survey_part} in already!"})

            #check if other steps to do first
            elif user.userinfo.completed_dialog or user.userinfo.completed_survey_part2:
                return Response(status=status.HTTP_403_FORBIDDEN, data={
                    "error": "NOT_YET_ALLOWED",
                    "error-message": f"You can't do that yet!"})

            success = save_survey_data(user_pk, survey_part, request.data)
            user.userinfo.completed_survey_part1 = success
            user.userinfo.save()

            if success:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ERROR": "SURVEY_NOT_SAVED",
                                      "error-message": f"{user.username}'s survey part {survey_part} data was not saved!"})

        else:
            #check if handed in aleady
            if user.userinfo.completed_survey_part2:
                return Response(status=status.HTTP_404_NOT_FOUND, data={
                    "error": "HANDED_IN_ALREADY",
                    "error-message": f"You handed survey {survey_part} in already!"})

            #check if other steps to do first
            elif not (user.userinfo.completed_survey_part1 and user.userinfo.completed_dialog):
                return Response(status=status.HTTP_404_NOT_FOUND, data={
                    "error": "NOT_YET_ALLOWED",
                    "error-message": f"You can't do that yet!"})

            success = save_survey_data(user_pk, survey_part, request.data)
            user.userinfo.completed_survey_part2 = success
            user.userinfo.save()

            if success:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={"ERROR": "SURVEY_NOT_SAVED",
                                      "error-message": f"{user.username}'s survey part {survey_part} data was not saved!"})

    if request.method == 'DELETE':

        try:
            user = User.objects.get(pk=int(user_pk))
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})

        user.userinfo.completed_survey_part2 = False
        user.userinfo.completed_dialog = False
        user.userinfo.save()

        return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def confirme_mail(request):
    if request.method == 'GET':
        try:  # to get user
            user = User.objects.get(username=request.data.get("username"))
            send_confirmation_email(user)
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})


@api_view(['POST'])
def get_chatdata(request):
    if request.method == 'POST':

        print("data: ", request.data)
        user_response_pk = request.data.get("user_response_pk", None)
        username = request.data.get("username", None)

        user = User.objects.get(username=username)
        history = []
        bot_responses = []
        choices = []

        if user_response_pk:
            print("RESPONSE, user responds to bot")
            user_response_graph_message = GraphMessage.objects.get(pk=user_response_pk)
            new_history_message = HistoryMessage(order_id=len(user.history.messages.all()) + 1,
                                                 history=user.history,
                                                 graph_message=user_response_graph_message)
            new_history_message.save()

            bot_response = user_response_graph_message.next.all()[0]
            last_bot_response, bot_responses = get_bot_messages(bot_response, user)

        else:
            if user.userinfo.last_bot_message_pk == -1:
                print("NEW CONVERSATION, user starts a new chat")

                ### choose start message
                # a user using DIALOG_STYLE_ONE_ON_ONE should only be greeted once
                # a user using any other dialog style should only be greeted by each module
                # choose the right start message based on the dialog style

                if user.userinfo.dialog_style == DIALOG_STYLE_ONE_ON_ONE:
                    start_message = GraphMessage.objects.filter(is_start=True, one_on_one=True)[0]
                else:
                    start_message = GraphMessage.objects.filter(is_start=True, one_on_one=False)[0]

                last_bot_response, bot_responses = get_bot_messages(start_message, user)

            else:
                print("HISTORY, user returned to conversation")
                history_messages = user.history.messages.all().order_by('order_id')
                for _history_message in history_messages:
                    history.append({"author": _history_message.graph_message.author,
                                    "content": _history_message.graph_message.content,
                                    "date": convert_to_localtime(_history_message.date)})
                last_bot_response = GraphMessage.objects.get(pk=user.userinfo.last_bot_message_pk)

        # return users' choices
        for user_res in last_bot_response.next.all():
            user_response = {
                "author": "USER",
                "pk": user_res.pk,
                "content": user_res.content
            }
            choices.append(user_response)

        response_data = {
            "history": history,
            "bot_responses": bot_responses,
            "choices": choices,
        }

        return Response(status=status.HTTP_200_OK, data=response_data)
