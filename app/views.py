from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import UserInfo, Dialog, GraphMessage
from django.contrib.auth import authenticate, login, logout
from django.core import serializers



@api_view(['GET', 'POST'])
def ok(request):
    if request.method == 'GET':
        return Response(status=status.HTTP_200_OK, data={"message": "OK"})

    if request.method == 'POST':
        try:
            User.objects.get(username="123")
        except User.DoesNotExist as e:
            print(e, "!!!!!!!!!!!")
        return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
def createuser(request):
    print(request.data)
    try:
        user = User.objects.create_user(username=request.data.get("email"), password=request.data.get("password"))
        user.save()

        userinfo = UserInfo(user=user, alias=request.data.get("username"))
        userinfo.save()

        dialog = Dialog(userinfo=userinfo, bot_type="BOT")
        dialog.save()

        print(f"User {user.username} created!")

        return Response(status=status.HTTP_200_OK)
    except IntegrityError as e:
        print(e)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})


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


@api_view(['GET'])
def getmessage(request):
    if request.method == 'GET':
        first_message = GraphMessage.objects.get(is_start=True)

        res = []
        for r in first_message.next.all():
            res.append({"pk": r.pk, "content": r.content})

        return Response(status=status.HTTP_200_OK, data={
            "success-message": f"XXX",
            "success": "SUCCESS",
            "message": {
                "message": first_message.content
            },
            "responds": res
        })
    