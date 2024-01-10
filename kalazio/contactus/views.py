from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from log.views import createLog
from user.models import User
from .models import ContactUs
from .serializers import ContactUsSerializer


# Create your views here.


# Create contact us
class ContactUsCreate(CreateAPIView):
    def post(self, request, *args, **kwargs):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # create log
            try:
                user = User.objects.get(pk=self.request.user.id).username
            except User.DoesNotExist:
                user = "anonymous"
            x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0]
            else:
                ip = self.request.META.get("REMOTE_ADDR")
            os_browser = self.request.META["HTTP_USER_AGENT"]
            createLog(
                "Post", user, "contactus/create/", ip, os_browser, serializer.data
            )
            # ----------------------------------------
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
