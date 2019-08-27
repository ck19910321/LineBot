from django.conf.urls import url, include, static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from webhooks import views
urlpatterns = [
    url(r'^callback/?', views.callback),
]