from django.db import models
from django.contrib.auth.models import User
from models import *
from rest_framework import serializers

class GraphMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=240)
    author = serializers.CharField(max_length=25)
    #prev =