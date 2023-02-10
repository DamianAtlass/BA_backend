from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError, Error
from .models import UserInfo, Dialog, GraphMessage, DialogMessage
from django.contrib.auth import authenticate, login, logout
from django.core import serializers



@api_view(['GET', 'POST'])
def ok(request):
    if request.method == 'GET':
        print(request.data)
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'POST':
        print(request.data)
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})


@api_view(['POST'])
def createuser(request):
    print(request.data)
    #create user
    try:
        new_user = User.objects.create_user(username=request.data.get("email"), password=request.data.get("password"))
        new_user.save()

        userinfo = UserInfo(user=new_user, alias=request.data.get("username"))
        userinfo.save()

        print(f"User {new_user.username} created!")

    except IntegrityError as e:
        print(e)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

    #create dialog
    try:
        new_dialog = Dialog(user=new_user, bot_type="BOT")
        new_dialog.save()
    except Error as e:
        print(e)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})

    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
def createadmin(request):
    superuser = User.objects.create_superuser("admin", "admin@admin.com", "123admin")
    superuser.save()
    print("Created admin")
    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def accounts(request):
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
            login(request, user)
            return Response(status=status.HTTP_200_OK, data={
                "success-message": f"Nutzer {user.userinfo.alias} erfolgreich eingeloggt ({user.is_authenticated})",
                "success": "LOGIN_SUCCESS"
            })
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={
                                "error-message": "Falsche Anmeldeinformationen.",
                                "error": "WRONG_CREDENTIALS"
                            })


@api_view(['POST'])
def get_chatdata(request):
    if request.method == 'POST':
        print("data: ", request.data)
        user_response_pk = request.data.get("user_response_pk", None)
        username = request.data.get("username", None)
        user = User.objects.get(username=username)

        get_history = False
        last_bot_response = None
        history = []
        choices = []
        bot_responses = []

        print(request.data)
        print("last_bot_message_pk: ", user.userinfo.last_bot_message_pk)
        if not user_response_pk and not user.userinfo.last_bot_message_pk == -1:
            print("returned to conversation")
            get_history = True
            last_bot_response = GraphMessage.objects.get(pk=user.userinfo.last_bot_message_pk)

        if get_history:
            print("HISTORY")
            dialog_messages = user.dialog.messages.all().order_by('order_id')

            for m in dialog_messages:
                history.append({"author": m.graph_message.author,
                                "content": m.graph_message.content})

        else:
            print("CHAT")
            if user_response_pk:
                # add user response to dialog
                user_response_graph_message = GraphMessage.objects.get(pk=user_response_pk)
                new_dialog_message = DialogMessage(order_id=len(user.dialog.messages.all())+1,
                                                   dialog=user.dialog,
                                                   graph_message=user_response_graph_message)
                new_dialog_message.save()

                bot_response = user_response_graph_message.next.all()[0]
                last_bot_response, bot_responses = get_bot_messages(bot_response, user)

            else:
                bot_response = GraphMessage.objects.get(is_start=True)
                last_bot_response, bot_responses = get_bot_messages(bot_response, user)
        # return users' choices
        for user_res in last_bot_response.next.all():
            user_response = {
                "author": "USER",
                "pk": user_res.pk,
                "content": user_res.content
            }
            print("response: ", user_response)
            choices.append(user_response)

        return Response(status=status.HTTP_200_OK, data={
            "history": history,
            "bot_responses": [] if get_history else bot_responses,
            "choices": choices,

        })


def get_bot_messages(bot_response: GraphMessage, user: User):
    bot_responses = []
    while True:
        #write dialog message in history
        new_dialog_message = DialogMessage(order_id=len(user.dialog.messages.all())+1,
                                           dialog=user.dialog,
                                           graph_message=bot_response)
        new_dialog_message.save()
        bot_responses.append({"author": bot_response.author,
                              "content": bot_response.content})

        # remember point in conversation
        user.userinfo.last_bot_message_pk = bot_response.pk
        user.userinfo.save()
        print("set user.userinfo.last_bot_message_pk to ", user.userinfo.last_bot_message_pk)
        if not bot_response.is_end and bot_response.next.all()[0].author == "BOT": #TODO make is_bot() function
            bot_response = bot_response.next.all()[0]
        else:
            return bot_response, bot_responses

