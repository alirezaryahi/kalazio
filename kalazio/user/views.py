import datetime
import re
import string
import datetime
import jdatetime
from django.utils.dateparse import parse_datetime
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
import base64
from log.views import createLog
from product.models import FavoriteProduct, Product, Warranty, Seller, ProductField
from product.serializers import FavoriteProductSerializer, FavoriteProductListSerializer
from .serializers import (
    NotificationSerializer,
    UserSerializer,
    GiftSerializerForList,
    UserEditSerializer
)
from .models import (
    Notifications,
    User,
    PhoneAuthenticated,
    Gift,
    Samava
)
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from .permissions import UserIsOwnerOrReadOnly
from questionAndAnswer.models import QuestionAndAnswer
from questionAndAnswer.serializers import QuestionAndAnswerSerializer
from order.models import Finally, Order, OrderItem
from order.serializers import OrderSerializer, OrderListSerializer
import time
import random
from kavenegar import *
from rest_framework.authtoken.models import Token
import requests

kave_api = KavenegarAPI('65456F4B654B4146357A54497A4B546A6F43414F384D7572537254484B395838')


# Create your views here.

# Get notification list :info
class NotificationList(ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        # create log
        try:
            user = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            user = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', user, 'user/notifications/', ip, os_browser)
        # ----------------------------------------
        notif = Notifications.objects.filter(user=self.request.user)
        serializer = NotificationSerializer(notif, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get favorite product list of user :info
class FavoriteOfUserList(ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            user = User.objects.get(pk=pk)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر موجود نمی باشد')
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'user/favorite-product-list/{pk}', ip, os_browser)
        # ----------------------------------------

        fav = FavoriteProduct.objects.filter(user=user)
        serializer = FavoriteProductListSerializer(fav, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Create favorite product list of user :info
class FavoriteOfUserCreate(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = FavoriteProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # create log
            try:
                user = User.objects.get(pk=self.request.user.id).username
            except User.DoesNotExist:
                user = 'anonymous'
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            os_browser = self.request.META['HTTP_USER_AGENT']
            createLog('Post', user, f'user/favorite-product-create/', ip, os_browser, serializer.data)
            # ----------------------------------------
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete item from favorite product list of user :info
class FavoriteOfUserDelete(DestroyAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def destroy(self, request, *args, **kwargs):
        pk = kwargs['pk']
        try:
            user = User.objects.get(pk=request.POST.get('user'))
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجو ندارد')
        try:
            obj = FavoriteProduct.objects.get(product=pk, user=user)
        # if FavoriteProduct does not exist :error
        except FavoriteProduct.DoesNotExist:
            return Response('محصول یافت نشد')
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Delete', userr, f'user/favorite-product-delete/{pk}', ip, os_browser, {'product': pk})
        # ----------------------------------------

        self.perform_destroy(obj)
        # return data :success
        return Response(status=status.HTTP_204_NO_CONTENT)


# Get question and answer of user :info
class QuestionAndAnswerOfUser(ListAPIView):
    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            user = User.objects.get(pk=pk)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد')
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'user/question-answer-user/{pk}', ip, os_browser)
        # ----------------------------------------

        question = QuestionAndAnswer.objects.filter(profile=user, confirm=True)
        serializer = QuestionAndAnswerSerializer(question, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get orders of user :info
class OrdersOfUser(ListAPIView):
    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        list = []
        try:
            user = User.objects.get(pk=pk)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد')
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'user/orders-user/{pk}', ip, os_browser)
        # ----------------------------------------
        orders = Order.objects.filter(user=user)
        for order in orders:
            if order.orderStatus == '6' or order.orderStatus == '4':
                list.append(order)
        serializer = OrderListSerializer(list, many=True)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)


# Login and register function :info
@api_view(['POST', ])
def user_login_register(request):
    for p in PhoneAuthenticated.objects.all():
        if p.created < time.time():
            p.delete()
    string = request.POST.get('string')
    # create log
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Post', 'anonymous', f'user/login-register/', ip, os_browser, {'username': string})
    # ----------------------------------------
    # Contact number should not be more or less than 11 digits :warning
    if len(string) > 11 or len(string) < 11:
        return Response('شماره تماس نباید بیشتر یا کمتر از 11 رقم باشد', status=status.HTTP_400_BAD_REQUEST)
    # Invalid contact number :warning
    if not string.startswith("09"):
        return Response('شماره تماس نامعتبر می باشد', status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username=string)
    # if user does not exist :error
    except User.DoesNotExist:
        user = User.objects.create(username=string)
        try:
            phone = PhoneAuthenticated.objects.get(phone=string)
        # if PhoneAuthenticated does not exist :error
        except PhoneAuthenticated.DoesNotExist:
            obj = PhoneAuthenticated(phone=string)
            obj.code = random.randrange(1000, 9999)
            obj.created = time.time() + 10800
            obj.save()
            object = PhoneAuthenticated.objects.get(phone=string)
            kave_api.sms_send({
                'receptor': obj.phone,
                'message': 'کد تایید شما از سایت کالازیو : ' + object.code
            })
            return Response('کد ارسال شد', status=status.HTTP_200_OK)
        # The code was sent :info
        if phone.created - 10800 + 120 < time.time():
            phone.delete()
            obj = PhoneAuthenticated(phone=string)
            obj.code = random.randrange(1000, 9999)
            obj.created = time.time() + 10800
            obj.save()
            object = PhoneAuthenticated.objects.get(phone=string)
            kave_api.sms_send({
                'receptor': obj.phone,
                'message': 'کد تایید شما از سایت کالازیو : ' + object.code
            })
            return Response('کد ارسال شد', status=status.HTTP_200_OK)
        # Your time to send the new code is 2 minutes :warning
        return Response('مدت زمان شما برای ارسال کد جدید 2 دقیقه می باشد', status=status.HTTP_400_BAD_REQUEST)
    try:
        phone = PhoneAuthenticated.objects.get(phone=user.username)
    # if PhoneAuthenticated does not exist :error
    except PhoneAuthenticated.DoesNotExist:
        obj = PhoneAuthenticated(phone=user.username)
        obj.code = random.randrange(1000, 9999)
        obj.created = time.time() + 10800
        obj.save()
        object = PhoneAuthenticated.objects.get(phone=user.username)
        kave_api.sms_send({
            'receptor': obj.phone,
            'message': 'کد تایید شما از سایت کالازیو : ' + object.code
        })
        return Response('کد ارسال شد', status=status.HTTP_200_OK)
    # The code was sent :info
    if phone.created - 10800 + 120 < time.time():
        phone.delete()
        obj = PhoneAuthenticated(phone=user.username)
        obj.code = random.randrange(1000, 9999)
        obj.created = time.time() + 10800
        obj.save()
        object = PhoneAuthenticated.objects.get(phone=user.username)
        kave_api.sms_send({
            'receptor': obj.phone,
            'message': 'کد تایید شما از سایت کالازیو : ' + object.code
        })
        return Response('کد ارسال شد', status=status.HTTP_200_OK)
    # Your time to send the new code is 2 minutes :warning
    return Response('مدت زمان شما برای ارسال کد جدید 2 دقیقه می باشد', status=status.HTTP_400_BAD_REQUEST)


# Check sms code for login :info
@api_view(['POST', ])
def user_login_check_code(request, *args, **kwargs):
    code = request.POST.get('code')
    string = request.POST.get('string')
    # create log
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Post', 'anonymous', f'user/login-code/', ip, os_browser,
              {'username': string, 'code': code,
               'cart-items': request.POST.get('cart-items') if request.POST.get('cart-items') else None})
    # ----------------------------------------
    # Contact number should not be more or less than 11 digits :warning
    if len(string) > 11 or len(string) < 11:
        return Response('شماره تماس نباید بیشتر یا کمتر از 11 رقم باشد', status=status.HTTP_400_BAD_REQUEST)
    # invalid contact number :warning
    if not string.startswith("09"):
        return Response('شماره تماس نامعتبر می باشد', status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username=string, join=True)
    # if user does not exist :error
    except User.DoesNotExist:
        try:
            user = User.objects.get(username=string, join=False)
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
        try:
            object = PhoneAuthenticated.objects.get(phone=string)
        # if PhoneAuthenticated does not exist :error
        except PhoneAuthenticated.DoesNotExist:
            return Response('شماره نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
        if object.created > time.time():
            if object.code == code:
                try:
                    token = Token.objects.get(user=user)
                # if token does not exist :error
                except Token.DoesNotExist:
                    token = Token.objects.create(user=user)
                object.delete()
                user.join = True
                user.save()

                # --------when user register-------------
                if request.POST.get('cart-items'):
                    cart_items = json.loads(request.POST.get('cart-items'))
                    order = None
                    try:
                        order = Order.objects.get(user=user, orderStatus='1')
                    except Order.DoesNotExist:
                        pass
                    if order:
                        for item in cart_items:
                            quantity = item['quantity']
                            try:
                                item = OrderItem.objects.get(productfield=ProductField.objects.get(pk=item['product']))
                            except OrderItem.DoesNotExist:
                                OrderItem.objects.create(order=order,
                                                         productfield=ProductField.objects.get(pk=int(item['product'])),
                                                         warranty=Warranty.objects.get(pk=int(item['warranty'])),
                                                         seller=Seller.objects.get(pk=int(item['seller'])),
                                                         quantity=int(item['quantity']))
                                return Response({'key': token.key}, status=status.HTTP_200_OK)
                            item.quantity += quantity
                            item.save()
                return Response({'key': token.key}, status=status.HTTP_200_OK)
        else:
            object.delete()
            user.delete()
            return Response('request is expired', status=status.HTTP_400_BAD_REQUEST)
    try:
        object = PhoneAuthenticated.objects.get(phone=string)
    # if PhoneAuthenticated does not exist :error
    except PhoneAuthenticated.DoesNotExist:
        return Response('شماره نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
    if object.created > time.time():
        if object.code == code:
            try:
                token = Token.objects.get(user=user)
            except Token.DoesNotExist:
                token = Token.objects.create(user=user)
            object.delete()
            # --------when user login-------------

            if request.POST.get('cart-items'):
                cart_items = json.loads(request.POST.get('cart-items'))
                order = None
                try:
                    order = Order.objects.get(user=user, orderStatus='1')
                # if order does not exist :error
                except Order.DoesNotExist:
                    pass
                if order:
                    for item in cart_items:
                        quantity = item['quantity']
                        try:
                            item = OrderItem.objects.get(productfield=ProductField.objects.get(pk=item['product']))
                        except OrderItem.DoesNotExist:
                            OrderItem.objects.create(order=order,
                                                     productfield=ProductField.objects.get(pk=int(item['product'])),
                                                     warranty=Warranty.objects.get(pk=int(item['warranty'])),
                                                     seller=Seller.objects.get(pk=int(item['seller'])),
                                                     quantity=int(item['quantity']))
                            return Response({'key': token.key}, status=status.HTTP_200_OK)
                        item.quantity += quantity
                        item.save()

            # -------------------------------------------
            return Response({'key': token.key}, status=status.HTTP_200_OK)
    # request is expired :warning
    else:
        object.delete()
        return Response('request is expired', status=status.HTTP_400_BAD_REQUEST)
    # invalid code :warning
    return Response('کد نا معتبر است', status=status.HTTP_400_BAD_REQUEST)


# Edit user info :info
class UserEdit(APIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def get(self, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.request.user.id, is_active=True)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'user/{user.pk}', ip, os_browser)
        # ----------------------------------------
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.request.user.id, is_active=True)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        serializer = UserEditSerializer(instance=user, data=request.data)
        if serializer.is_valid():
            if self.request.POST.get('newsletters'):
                newsletters = True if self.request.POST.get('newsletters') == 'true' else False
            if not self.request.POST.get('newsletters'):
                newsletters = user.newsletters
            # change serializer time to jalali date :info
            try:
                dateOfBirth = jdatetime.datetime(serializer.validated_data['dateOfBirth'].year,
                                                 serializer.validated_data['dateOfBirth'].month,
                                                 serializer.validated_data['dateOfBirth'].day)
            except:
                dateOfBirth = user.dateOfBirth
            if self.request.POST.get('codeMelli'):
                # You are not allowed to change the national code :warning
                if user.authorized == 'confirm':
                    return Response('شما اجازه تغییر کد ملی را ندارید', status=status.HTTP_400_BAD_REQUEST)
                serializer.save(is_active=True, active=True, dateOfBirth=dateOfBirth, newsletters=newsletters,
                                codeMelli=self.request.POST.get('codeMelli'))
                # create log
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = self.request.META.get('REMOTE_ADDR')
                os_browser = self.request.META['HTTP_USER_AGENT']
                createLog('Put', userr, f'user/{user.pk}', ip, os_browser, serializer.data)
                # ----------------------------------------
                user.authorized = 'pending'
                user.save()
            else:
                serializer.save(is_active=True, active=True, dateOfBirth=dateOfBirth, newsletters=newsletters)
            # return data :success
            return Response(serializer.data, status=status.HTTP_200_OK)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Buy gift by user :info
class UserGiftBuy(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.request.user.id, join=True)
            userr = user.username
        # if user does not exist :error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'gift-list-buy/{user.pk}', ip, os_browser)
        # ---------------------------------------
        gift = Gift.objects.filter(donator=user)
        serializer = GiftSerializerForList(gift, many=True)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get list of receive gift : info
class UserGiftReceive(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(pk=self.request.user.id, active=True)
            userr = user.username
        # if user does not exist : error
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'gift-list-receive/{user.pk}', ip, os_browser)
        # ----------------------------------------
        gift = Gift.objects.filter(user=user)
        serializer = GiftSerializerForList(gift, many=True)
        # return data : success
        return Response(serializer.data, status=status.HTTP_200_OK)


# Refresh shahkar token if expired :thirdparty
# def refresh_token(request):
#     authorization = "Basic aXJhbml5YW5DbGllbnQ6U1pHSnFPZnZYMjh5aWVuUg=="
#     shahkar = Shahkar.objects.all().first()
#     refresh_token = shahkar.refresh_token
#     grant_type = "refresh_token"
#     now = timezone.now()
#     res = requests.post(f'https://pgsb.iran.gov.ir/oauth/token?grant_type={grant_type}&refresh_token={refresh_token}',
#                         headers={"Authorization": authorization})
#     shahkar = Shahkar.objects.get(refresh_token=refresh_token)
#     try:
#         shahkar.access_token = res.json()['access_token']
#     except:
#         authorization = "Basic aXJhbml5YW5DbGllbnQ6U1pHSnFPZnZYMjh5aWVuUg=="
#         username = "iraniyan"
#         password = "Iraniyan@1473"
#         grant_type = "password"
#         res = requests.post(
#             f'https://pgsb.iran.gov.ir/oauth/token?grant_type={grant_type}&username={username}&password={password}',
#             headers={"Authorization": authorization})
#         Shahkar.objects.all().delete()
#         shahkar = Shahkar.objects.create(refresh_token=res.json()['refresh_token'])
#         shahkar.access_token = res.json()['access_token']
#         shahkar.expire = now + datetime.timedelta(seconds=res.json()['expires_in'])
#         shahkar.save()
#         return id_maching(request)
#     shahkar.expire = now + datetime.timedelta(seconds=res.json()['expires_in'])
#     shahkar.save()
#     return id_maching(request)


# Get shahkar token :thirdparty
# @api_view(['POST', ])
# @permission_classes([IsAuthenticated])
# def get_token(request):
#     authorization = "Basic aXJhbml5YW5DbGllbnQ6U1pHSnFPZnZYMjh5aWVuUg=="
#     username = "iraniyan"
#     password = "Iraniyan@1473"
#     grant_type = "password"
#     objects = Shahkar.objects.all().first()
#     now = timezone.now()
#     if objects:
#         if now > objects.expire:
#             return refresh_token(request)
#         return id_maching(request)
#
#     res = requests.post(
#         f'https://pgsb.iran.gov.ir/oauth/token?grant_type={grant_type}&username={username}&password={password}',
#         headers={"Authorization": authorization})
#     try:
#         shahkar = Shahkar.objects.get(refresh_token=res.json()['refresh_token'])
#     # if Shahkar does not exist
#     except Shahkar.DoesNotExist:
#         Shahkar.objects.all().delete()
#         shahkar = Shahkar.objects.create(refresh_token=res.json()['refresh_token'])
#     shahkar.access_token = res.json()['access_token']
#     shahkar.expire = now + datetime.timedelta(seconds=res.json()['expires_in'])
#     shahkar.save()
#     return id_maching(request)
#
#
# # Ckeck code melli by shahkar :thirdparty
# @permission_classes([IsAuthenticated])
# def id_maching(request):
#     objects = Shahkar.objects.all().first()
#     authorization = f'Bearer {objects.access_token}'
#     basicAuthorization = "Basic a2FsYXppb19nc2I6S0BsQXppMCMkOTE="
#     pid = "5dfa246bb6c8160317ac753e"
#     now = datetime.datetime.now()
#     id = datetime.datetime.strftime(now, '0563%Y%m%d%H%M%S%f')
#     res = requests.post('https://pgsb.iran.gov.ir/api/client/apim/v1/shahkar/gwsh/serviceIDmatching',
#                         headers={"Authorization": authorization, "Content-Type": "application/json",
#                                  "basicAuthorization": basicAuthorization, "pid": pid},
#                         json={"requestId": id,
#                               "serviceNumber": request.POST.get('serviceNumber'),
#                               "serviceType": 2,
#                               "identificationType": 0,
#                               "identificationNo": request.POST.get('identificationNo')})
#     noww = timezone.now()
#     user = request.user
#     if not user.register_date or user.register_date.date() < noww.date():
#         user.register_date = now
#         user.register_number = 0
#         user.save()
#     if user.register_number < 50:
#         if res.json()['result']['data']['response'] == 200:
#             user.authorized = 'confirm'
#             user.codeMelli = request.POST.get('identificationNo')
#             user.save()
#         if res.json()['result']['data']['response'] == 311:
#             user.authorized = 'deny'
#             user.codeMelli = request.POST.get('identificationNo')
#             user.register_number += 1
#             user.save()
#         if res.json()['result']['data']['response'] == 600:
#             user.authorized = 'deny'
#             user.codeMelli = request.POST.get('identificationNo')
#             user.register_number += 1
#             user.save()
#     # The number of times the national code is registered in the masterpiece system is allowed for you today more than the ceiling, please try again in the next few days.
#     else:
#         return Response(
#             'تعداد دفعات ثبت کد ملی در سامانه شاهکار برای شما امروز بیش از سقف مجاز است،لطفا در روزهای بعد مجددا تلاش کنید',
#             status=status.HTTP_400_BAD_REQUEST)
#     return Response(res.json(), status=res.status_code)


@permission_classes([IsAuthenticated])
@api_view(['POST', ])
def get_samava_url(request):
    user = request.user.username
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Post', user, 'user/get-samava-url/', ip, os_browser)
    # ----------------------------------------
    client_id = "gostaresh_kalazio@samava"
    client_secret = "xWa6XiZPKOEvwddUb26vvV216KflL3RKx6LT64TtmrTuWc256Y"
    scopes = ["mobile_number"]
    redirect_uri = "https://kalazio.ir/shahkar/verify"
    state = (''.join(random.choices(string.ascii_lowercase, k=32)))
    loa = "LEVEL_2_2"
    mobile_number = request.user.username
    try:
        samava = Samava.objects.get(phone=request.user.username, expire=False)
    except Samava.DoesNotExist:
        req = requests.post('https://idbtob.iran.ir/oauth/create_authorize',
                            headers={"Content-Type": "application/json"},
                            json={"client_id": client_id, "client_secret": client_secret, "scopes": scopes,
                                  "redirect_uri": redirect_uri, "state": state, "loa": loa,
                                  "mobile_number": mobile_number})
        new_samava = Samava.objects.create(authorize_url=req.json()['authorize_url'],
                                           b2b_base_url=req.json()['b2b_base_url'], state=state,
                                           secure_code=req.json()['secure_code'], phone=request.user.username)
        new_samava.count += 1
        new_samava.save()
        return Response(new_samava.authorize_url, status=status.HTTP_200_OK)
    if samava.access_token:
        creation_time = datetime.datetime.strptime(samava.creation_time, "%Y-%m-%d %H:%M:%S.%f")
        if datetime.datetime.now() < creation_time + datetime.timedelta(seconds=samava.expires_in):
            return Response('توکن ولید می باشد', status=status.HTTP_200_OK)
    if timezone.now() > samava.time + datetime.timedelta(minutes=5) or samava.count >= 2:
        samava.expire = True
        samava.save()
        req = requests.post('https://idbtob.iran.ir/oauth/create_authorize',
                            headers={"Content-Type": "application/json"},
                            json={"client_id": client_id, "client_secret": client_secret, "scopes": scopes,
                                  "redirect_uri": redirect_uri, "state": state, "loa": loa,
                                  "mobile_number": mobile_number})
        new_samava = Samava.objects.create(authorize_url=req.json()['authorize_url'], state=state,
                                           b2b_base_url=req.json()['b2b_base_url'],
                                           secure_code=req.json()['secure_code'], phone=request.user.username)
        new_samava.count += 1
        new_samava.save()
        return Response(new_samava.authorize_url, status=status.HTTP_200_OK)
    else:
        samava.count += 1
        samava.save()
        return Response(samava.authorize_url, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['POST', ])
def get_samava_token(request):
    error = request.POST.get('error')
    state = request.POST.get('state')
    code = request.POST.get('code')
    user = request.user.username
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Post', user, 'user/get-samava-token/', ip, os_browser, {'error': error, 'code': code, 'state': state})
    # ----------------------------------------
    samava = Samava.objects.get(phone=request.user.username, expire=False)
    if samava.access_token:
        creation_time = datetime.datetime.strptime(samava.creation_time, "%Y-%m-%d %H:%M:%S.%f")
        if datetime.datetime.now() < creation_time + datetime.timedelta(seconds=samava.expires_in):
            return Response('توکن ولید می باشد', status=status.HTTP_200_OK)
        return Response('تاریخ انقضا توکن به پایان رسیده است', status=status.HTTP_200_OK)
    redirect_uri = "https://kalazio.ir/shahkar/verify"
    if not error and not state:
        return Response('پارامترها به درستی ارسال نشده است', status=status.HTTP_400_BAD_REQUEST)
    if error and state:
        return Response('پارامترها به درستی ارسال نشده است', status=status.HTTP_400_BAD_REQUEST)
    if error:
        samava.expire = True
        samava.save()
        return Response('با مشکل مواجه شدن فرایند احراز هویت', status=status.HTTP_200_OK)
    if samava.state != state or timezone.now() > samava.time + datetime.timedelta(minutes=9):
        samava.expire = True
        samava.save()
        return Response('با مشکل مواجه شدن فرایند احراز هویت', status=status.HTTP_200_OK)
    samava.code = code
    samava.save()
    headers = {
        'Authorization': 'Basic Z29zdGFyZXNoX2thbGF6aW9Ac2FtYXZhOnhXYTZYaVpQS09FdndkZFViMjZ2dlYyMTZLZmxMM1JLeDZMVDY0VHRtclR1V2MyNTZZ',
        'Content-Type': 'application/x-www-form-urlencoded',

    }
    data = f"grant_type=authorization_code&secure_code={samava.secure_code}&code={samava.code}&redirect_uri={redirect_uri}"

    url = "https://idbtob.iran.ir/oauth/token"
    req = requests.request("POST", url, headers=headers, data=data)
    if req.status_code == 200:
        token = req.json()["access_token"]
        if check_token(token, request):
            samava.jti = req.json()['jti']
            samava.expires_in = req.json()['expires_in']
            samava.creation_time = req.json()['creation_time']
            samava.access_token = token
            samava.save()
            return Response("با موفقیت ثبت شد", status=status.HTTP_200_OK)
        else:
            samava.expire = True
            samava.save()
            return Response("توکن معتبر نمی‌باشد", status=status.HTTP_409_CONFLICT)
    samava.expire = True
    samava.save()
    return Response(req.json()["error_reason"], status=req.json()["status"])


def check_token(token, request):
    headers = {
        'Authorization': 'Basic Z29zdGFyZXNoX2thbGF6aW9Ac2FtYXZhOnhXYTZYaVpQS09FdndkZFViMjZ2dlYyMTZLZmxMM1JLeDZMVDY0VHRtclR1V2MyNTZZ',
        'Content-Type': 'application/x-www-form-urlencoded',

    }
    data = f"token={token}"

    url = "https://idbtob.iran.ir/oauth/check_token"
    req = requests.request("POST", url, headers=headers, data=data)
    return req.json()["active"]
