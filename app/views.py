from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError, Error

from .helper import convert_to_localtime
from .models import UserInfo, History, GraphMessage, HistoryMessage
from django.contrib.auth import authenticate, login as django_login, logout
from datetime import datetime
from django.utils import timezone
import pytz


INITIAL_USER = "INITIAL_USER"
# dialog styles
DIALOG_STYLE_ONE_ON_ONE = "ONE_ON_ONE"
DIALOG_STYLE_COLORED_BUBBLES = "COLORED_BUBBLES"
DIALOG_STYLE_CLASSIC_GROUP = "CLASSIC_GROUP"
DIALOG_STYLE_PICTURE = "PROFILE_PICTURES"


@api_view(['GET', 'POST'])
def ok(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'POST':
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
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            User.objects.get(username=username)
        except User.DoesNotExist as e:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error-message": "Diese Email ist nicht in der Datenbank.",
                                "error": "USER_NOT_FOUND"
                            })

        user = authenticate(request, username=username, password=password)

        if user is not None:
            django_login(request, user)
            return Response(status=status.HTTP_200_OK, data={
                "success-message": f"Nutzer {user.username} erfolgreich eingeloggt ({user.is_authenticated})",
                "success": "LOGIN_SUCCESS",
                "dialog_style": user.userinfo.dialog_style,
                "user_pk": user.pk,
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
        # create user
        try:
            new_user = User.objects.create_user(username=request.data.get("username"), password=request.data.get("password"))
            new_user.save()

            dialog_style = ""
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

            userinfo = UserInfo(user=new_user, email=request.data.get("email"), dialog_style=dialog_style)
            userinfo.save()

            print(f"User {new_user.username} created!")

        except IntegrityError as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

        # create history
        try:
            new_history = History(user=new_user, bot_type="BOT")
            new_history.save()
        except Error as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

        return Response(status=status.HTTP_200_OK)

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


@api_view(['DELETE'])
def history(request):
    if request.method == 'DELETE':
        print(request.data)
        username = request.data.get("username", None)
        user = User.objects.get(username=username)

        user.userinfo.last_bot_message_pk = -1
        user.userinfo.save()
        try:
            user.history.delete()
        except History.DoesNotExist as e:
            print(e)
            pass
        else:
            print(f"History of {username} was successfully deleted!")
        new_history = History(user=User.objects.get(username=username), bot_type="BOT")
        new_history.save()

        return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def foo(request, username=None):
    print("HERE", request.GET.get('q', 'default'))
    if request.method == 'POST':
        print("username:", username)
        return Response(status=status.HTTP_200_OK)


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

        print("######timezone time now:", convert_to_localtime(timezone.now()))

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
                              "date": convert_to_localtime(datetime.now()),
                              "dialogIsComplete": bot_response.is_end})

        # remember point in conversation
        user.userinfo.last_bot_message_pk = bot_response.pk
        user.userinfo.save()
        if not bot_response.is_end and not bot_response.next.all()[0].author == "USER": #TODO make is_bot() function
            bot_response = bot_response.next.all()[0]
        else:
            return bot_response, bot_responses
