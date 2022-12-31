from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from .models import UserInfo


@api_view(['GET'])
def ok(request):
    if request.method == 'GET':
        return Response(status=status.HTTP_200_OK)

@api_view(['Get'])
def createuser(request):
    try:
        user = User.objects.create_user(username=request.data.get("email"), password=request.data.get("password"))
        user.save()

        userinfo = UserInfo(user=user, alias="ben")
        userinfo.save()
        return Response(status=status.HTTP_200_OK)
    except IntegrityError as e:
        user = User.objects.get(username=request.data.get("email"))
        print(user.userinfo.user)
        user.delete()





        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"error": str(e)})
