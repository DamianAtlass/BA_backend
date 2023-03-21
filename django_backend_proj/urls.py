"""django_backend_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r"api/ok/", views.ok),
    re_path(r"api/login/", views.login),
    re_path(r"api/adminlogin/", views.adminlogin),
    re_path(r"api/admin/getuserdata/", views.getuserdata),
    #re_path(r"api/createadmin/", views.createadmin),
    path("api/accounts/", include("django.contrib.auth.urls")),
    re_path(r"api/accounts/score/(?P<user_pk>\d{3})/$", views.score),
    re_path("api/accounts/", views.accounts),
    #re_path("api/history/", views.history),
    re_path(r'api/surveydata/(?P<user_pk>\d{3})/(?P<survey_part>\d{1})/$', views.survey_data),
    re_path("api/getchatdata/", views.get_chatdata),
    re_path("api/verifytoken/", views.verify_token_view),
    re_path(r"api/invite/(?P<user_pk>\d{3})/$", views.invite),
    re_path(r"api/sendreminder/", views.send_reminder),
]
