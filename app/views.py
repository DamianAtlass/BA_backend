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
        get_history = request.data.get("get_history", False)
        username = request.data.get("username", None)
        user = User.objects.get(username=username)

        print(request.data)
        # if bot message targeted (just for developing)
        if user_response_pk and not GraphMessage.objects.get(pk=user_response_pk).author == "USER":
            print("Message was not from USER!")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        history = []
        choices = []

        if get_history:
            dialog_messages = user.dialog.messages.all().order_by('order_id')

            for m in dialog_messages:
                history.append({"author": m.graph_message.author,
                                "content": m.graph_message.content})

        if user_response_pk:
            # add user response to dialog
            user_response_graph_message = GraphMessage.objects.get(pk=user_response_pk)
            new_dialog_message = DialogMessage(order_id=len(user.dialog.messages.all())+1,
                                               dialog=user.dialog,
                                               graph_message=user_response_graph_message)
            new_dialog_message.save()

            bot_response = user_response_graph_message.next.all()[0]
            bot_response, bot_responses = get_bot_messages(bot_response, user)

        else:
            bot_response = GraphMessage.objects.get(is_start=True)
            bot_response, bot_responses = get_bot_messages(bot_response, user)

        for res in bot_response.next.all():
            user_response = {
                "author": "USER",
                "pk": res.pk,
                "content": res.content
            }
            print("response: ", user_response)
            choices.append(user_response)

        return Response(status=status.HTTP_200_OK, data={
            "history": history,
            "bot_responses": bot_responses,
            "choices": choices,

        })


def get_bot_messages(bot_response: GraphMessage, user: User):
    bot_responses = []
    while True:
        new_dialog_message = DialogMessage(order_id=len(user.dialog.messages.all())+1,
                                           dialog=user.dialog,
                                           graph_message=bot_response)
        new_dialog_message.save()
        bot_responses.append({"author": bot_response.author,
                              "content": bot_response.content})

        if not bot_response.is_end and bot_response.next.all()[0].author == "BOT": #TODO make is_bot() function
            bot_response = bot_response.next.all()[0]
        else:
            return bot_response, bot_responses

