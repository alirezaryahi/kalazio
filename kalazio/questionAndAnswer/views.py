from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from adminPanel.models import SellerRepresentative
from log.views import createLog
from product.models import ProductField
from user.models import User
from user.permissions import UserIsOwnerOrReadOnly
from .serializers import (
    QuestionAndAnswerSerializerForCreate,
    QuestionAndAnswerSerializerForQuestion,
    QuestionAndAnswerSerializerForAnswer,
)
from .models import QuestionAndAnswer


# Create your views here.


# Create question and answers :info
class QuestionAndAnswerCreate(CreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = QuestionAndAnswerSerializerForCreate(data=request.data)
        if serializer.is_valid():
            field = ProductField.objects.get(
                product=serializer.validated_data["product"]
            )
            if serializer.validated_data["parent"]:
                # Only the seller of the product has the ability to respond :warning
                if self.request.user != field.seller.sellerRepresentative.user:
                    return Response(
                        "تنها فروشنده محصول قابلیت پاسخ را دارد",
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            serializer.save(user=self.request.user)
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
                "Post",
                user,
                "questionAndAnswer/question-answer-create/",
                ip,
                os_browser,
                serializer.data,
            )
            # ----------------------------------------
            # return data :success
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get my questions :info
class MyQuestion(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        objects = QuestionAndAnswer.objects.filter(
            user=self.request.user, parent=None, confirm=True
        )
        serializer = QuestionAndAnswerSerializerForQuestion(objects, many=True)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get my answers :info
class MyAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        list = []
        objects = QuestionAndAnswer.objects.filter(user=self.request.user, confirm=True)
        for obj in objects:
            if obj.parent is not None:
                list.append(obj)
        serializer = QuestionAndAnswerSerializerForAnswer(list, many=True)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)
