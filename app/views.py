from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .helper import convert_to_localtime, save_survey_data, send_confirmation_email
from .models import UserInfo, History, GraphMessage, HistoryMessage
from django.contrib.auth import authenticate, login as django_login
from datetime import datetime
import random

INITIAL_USER = "INITIAL_USER"
# dialog styles
DIALOG_STYLE_ONE_ON_ONE = "ONE_ON_ONE"
DIALOG_STYLE_COLORED_BUBBLES = "COLORED_BUBBLES"
DIALOG_STYLE_CLASSIC_GROUP = "CLASSIC_GROUP"
DIALOG_STYLE_PICTURE = "PROFILE_PICTURES"


@api_view(['GET', 'POST'])
def ok(request, user_pk="default"):
    if request.method == 'GET':
        print(request.data)
        for user in User.objects.all():
            print(f"User {user.username}: {user.pk}")
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'POST':
        print(user_pk)
        print(request.data)
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})


@api_view(['POST'])
def createadmin(request):
    superuser = User.objects.create_superuser("admin", "admin@admin.com", "123admin")
    superuser.save()
    print("Created admin")
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def login(request):
    print("LOGIN ATTEMPT")
    if request.method == 'POST':
        print(request.data)
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={
                                "error-message": "Diese Email ist nicht in der Datenbank.",
                                "error": "USER_NOT_FOUND",
                            })

        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is not None:
            django_login(request, authenticated_user)

            if authenticated_user.userinfo.verified:
                return Response(status=status.HTTP_200_OK, data={
                    "success": "LOGIN_SUCCESS",
                    "dialog_style": authenticated_user.userinfo.dialog_style,
                    "username": authenticated_user.username,
                    "user_pk": authenticated_user.pk,
                    "completed_dialog": authenticated_user.userinfo.completed_dialog,
                    "completed_survey": authenticated_user.userinfo.completed_survey,
                })
            else:
                verification_code = request.data.get("verification_code")
                if verification_code:
                    verification_code = int(verification_code)
                    if verification_code == authenticated_user.userinfo.verification_code:
                        authenticated_user.userinfo.verified = True
                        authenticated_user.userinfo.save()
                        return Response(status=status.HTTP_200_OK, data={
                            "success": "LOGIN_SUCCESS",
                            "dialog_style": authenticated_user.userinfo.dialog_style,
                            "username": authenticated_user.username,
                            "user_pk": authenticated_user.pk,
                            "completed_dialog": authenticated_user.userinfo.completed_dialog,
                            "completed_survey": authenticated_user.userinfo.completed_survey,
                        })
                    else:
                        return Response(status=status.HTTP_401_UNAUTHORIZED,
                                        data={
                                            "error-message": f"Wrong verification code.",
                                            "error": "WRONG_VERIFICATION_CODE"
                                        })

                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED,
                                    data={
                                        "error-message": f"Please enter your verification code that was sent to {authenticated_user.userinfo.email}.",
                                        "error": "VERIFICATION_NECESSARY"
                                    })
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error-message": "Falsche Anmeldeinformationen.",
                                "error": "WRONG_CREDENTIALS"
                            })


@api_view(['POST', 'DELETE'])
def accounts(request):
    if request.method == 'POST':
        print(request.data)

        ###check if email exists in userinfo before actuall user is created

        try:
            UserInfo.objects.get(email=request.data.get("email"))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={"error": "EMAIL_NOT_UNIQUE",
                                  "error-message": "Email is already in use!"})
        except UserInfo.DoesNotExist as e:
            pass

        ### create user
        try:
            new_user = User.objects.create_user(username=request.data.get("username"),
                                                password=request.data.get("password"))
            new_user.save()
            print(f"User {new_user.username} created!")

        except IntegrityError as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={"error": str(e),
                                  "error-message": "Username already taken!"})

        ### create userinfo
        #TODO: calculate dialog style randomly
        match request.data.get("email"):
            case "alice@mail.com":
                dialog_style = DIALOG_STYLE_ONE_ON_ONE
            case "ben@mail.com":
                dialog_style = DIALOG_STYLE_COLORED_BUBBLES
            case "christian@mail.de":
                dialog_style = DIALOG_STYLE_COLORED_BUBBLES
            case "daniel@mail.de":
                dialog_style = DIALOG_STYLE_COLORED_BUBBLES
            case _:
                dialog_style = DIALOG_STYLE_ONE_ON_ONE

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

                if not inviting_user.userinfo.completed_survey:
                    return Response(status=status.HTTP_400_BAD_REQUEST,
                                    data={"error": "Inviting user needs to hand in the survey first!"})

                new_user.userinfo.invited_by = inviting_user
                new_user.userinfo.save()
            except User.DoesNotExist as e:
                print("Error:", e, "Inviting user does not exist!")

        # try to send verification email
        try:
            result = send_confirmation_email(new_user)

            #sending process was not successfull
            if not result == 1:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": "Sending email went wrong!"})

        #TODO specify if an exception ever occurs
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

        return Response(status=status.HTTP_201_CREATED,
                        data={"success-message": (f"Account created! An email was sent to {new_user.userinfo.email}. "
                                                  "You can close this window now.")})

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
            print("found user")
            return Response(status=status.HTTP_200_OK, data={"inviting_user": inviting_user.username})
        except User.DoesNotExist as e:
            print("didnt found user")
            return Response(status=status.HTTP_404_NOT_FOUND,
                            data={"error": str(e),
                                  "error-message": "Inviting user does not exist! Bad link!"})




@api_view(['DELETE'])
def history(request):
    if request.method == 'DELETE':
        print(request.data)
        username = request.data.get("username", None)
        user = User.objects.get(username=username)

        user.userinfo.last_bot_message_pk = -1
        user.userinfo.completed_survey = True
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
def survey_data(request, user_pk=""):
    if request.method == 'POST':
        #check if user exists & if data has already been sent
        try:
            user = User.objects.get(pk=int(user_pk))
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})

        # check if survey has been handed in already
        if not user.userinfo.completed_survey:

            success = save_survey_data(user_pk, request.data)
            user.userinfo.completed_survey = success
            user.userinfo.save()

            if success:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": f"{user.username}'s survey data was not saved!"})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"error": f"{user.username} handed a survey in already!"})

    if request.method == 'DELETE':

        try:
            user = User.objects.get(pk=int(user_pk))
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND, data={"error": str(e)})

        user.userinfo.completed_survey = False
        user.userinfo.completed_dialog = False
        user.userinfo.save()

        return Response(status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def confirme_mail(request):
    if request.method == 'GET':
        try: #to get user
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

        if username == INITIAL_USER:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                bot_response = GraphMessage.objects.get(is_start=True)
                last_bot_response, bot_responses = get_bot_messages(bot_response, user)

            else:
                print("HISTORY, user returned to conversation")
                history_messages = user.history.messages.all().order_by('order_id')
                for m in history_messages:
                    history.append({"author": m.graph_message.author,
                                    "content": m.graph_message.content,
                                    "date": convert_to_localtime(m.date)})
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
            return bot_response, bot_responses
        else:
            if bot_response.next.all()[0].author == "USER":
                return bot_response, bot_responses
            else:
                bot_response = bot_response.next.all()[0]

