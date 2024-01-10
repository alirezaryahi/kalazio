import datetime
import base64, requests
import math
from rest_framework.authtoken.models import Token
import uuid
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError

from Kalazio.pagination import StandardResultsSetPagination
from log.views import createLog
from . import models
from django.http import HttpRequest as req
from Crypto.Cipher import DES3
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, DestroyAPIView, \
    RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from adminPanel.models import SellerRepresentative, Partner
from product.models import Product, Visited, Warranty, Seller, ProductField, UserEvidence, ProductFieldFeaturesValue
from product.serializers import ProductSerializer
from user.models import User, Gift
from user.serializers import GiftSerializerForOrder
from user.permissions import UserIsOwnerOrReadOnly
from .models import Address, Order, OrderItem, State, City, Finally, NextOrderItem, Send
from .serializers import (
    AddressSerializerRet,
    AddressSerializer,
    OrderSerializer,
    OrderItemSerializer,
    OrderItemListSerializer,
    FinallySerializer,
    CancelOrderSerializer,
    NextOrderItemSerializer,
    NextOrderItemListSerializer,
    StateSerializer,
    CitySerializer,
    GetCompleteOrderSerializer,
    FinallySerializerForList,
    OrderSerializerForOrders,
    OrderListSerializer,
    OrderItemListSerializerForOrderList,
    AddressSerializerRetForEdit
)
from kavenegar import *

kave_api = KavenegarAPI('65456F4B654B4146357A54497A4B546A6F43414F384D7572537254484B395838')
import jdatetime
from dateutil import parser


# Create your views here.


def pad(text, pad_size=16):
    text_length = len(text)
    last_block_size = text_length % pad_size
    remaining_space = pad_size - last_block_size
    text = text + (remaining_space * chr(remaining_space))
    return text


def encrypt_des3(text):
    secret_key_bytes = base64.b64decode(settings.SADAD_SECRET_KEY)
    text = pad(text, 8)
    cipher = DES3.new(secret_key_bytes, DES3.MODE_ECB)
    cipher_text = cipher.encrypt(str.encode(text))
    return base64.b64encode(cipher_text).decode("utf-8")


def encrypt_request_payment_data(terminal_id, tracking_code, amount):
    text = terminal_id + ';' + str(tracking_code) + ';' + str(amount)
    sign_data = encrypt_des3(text)
    return sign_data


# tashim
def define_multiplexing_data(final):
    list = []
    list2 = []
    for item in final.order.orderOrderitem.all():
        partners = Partner.objects.all()
        commision_amount = round(
            (item.productfield.get_price_after_discount_and_taxation() * item.productfield.field.commission) / 100)
        seller_amount = round(
            item.productfield.get_price_after_discount_and_taxation() - (
                    (
                            item.productfield.get_price_after_discount_and_taxation() * item.productfield.field.commission) / 100))
        sum_commision = 0
        for partner in partners:
            sum_commision += round((commision_amount * partner.percent) / 100)
            list.append({
                'type': 'partner',
                'partner': partner,
                'quantity': item.quantity,
                'amount': round((commision_amount * partner.percent) / 100)
            })
        kalazio_amount = commision_amount - sum_commision
        list.append({
            'type': 'seller',
            'partner': item.seller,
            'quantity': item.quantity,
            'amount': seller_amount
        })
        list.append({
            'type': 'کارگزاری کالازیو',
            'quantity': item.quantity,
            'amount': kalazio_amount
        })
    for li in list:
        if li['type'] == 'کارگزاری کالازیو':
            list2.append({
                'IbanNumber': 'IR660170000000111889412008',
                'Value': li['amount'] * li['quantity']
            })
        if li['type'] == 'seller':
            list2.append({
                'IbanNumber': li['partner'].shebaNumber,
                'Value': li['amount'] * li['quantity']
            })
        if li['type'] == 'partner':
            list2.append({
                'IbanNumber': li['partner'].ibanNumber,
                'Value': li['amount'] * li['quantity']
            })
    if final.order.sendPrice:
        list2.append({
            'IbanNumber': 'IR660170000000111889412008',
            'Value': final.order.sendPrice
        })

    data = {
        'Type': 'Amount',
        'MultiplexingRows': list2,
    }
    return data


# generate payment link
@api_view(['POST'])
def create_finally(request):
    list = []
    confirm_list = []
    serialized_data = None
    confirm_list2 = ''
    status = ''
    objects = Finally.objects.filter(user=request.user)
    if objects:
        for object in objects:
            time = object.time + datetime.timedelta(minutes=300)
            now1 = timezone.now()
            if (object.order.orderStatus == '3' or object.order.orderStatus == '10') and now1 > time:
                object.order.orderStatus = '7'
                object.order.save()
                for item in object.order.orderOrderitem.all():
                    item.productfield.inventory += item.quantity
                    item.productfield.save()
                return Response('زمان شما برای پرداخت این سفارش به پایان رسیده است و سفارش شما لفو شده است')
            if object.order.orderStatus == '2' and now1 > time:
                object.order.orderStatus = '9'
                object.order.save()
                for item in object.order.orderOrderitem.all():
                    item.productfield.inventory += item.quantity
                    item.productfield.save()
                return Response('فروشنده در زمان تعیین شده سفارش شما را تایید نکرده است و سفارش شما لفو شده است')
    order = None
    PostTracking = None
    order = Order.objects.filter(
        (Q(orderStatus='1') or Q(orderStatus='3') or Q(orderStatus='10')) and Q(user=request.user)).last()
    try:
        finall = Finally.objects.get(order=order)
    # if finally does not exist
    except Finally.DoesNotExist:
        # if cart is empty
        if not order.get_total_price():
            return Response('سبد خرید شما خالی است')
        serializer = FinallySerializer(data=request.data)
        if serializer.is_valid():
            for item in order.orderOrderitem.all():
                if item.productfield.inventory < item.quantity:
                    return Response(f'موجودی محصول {item.productfield} بیش از تعداد خرید شما می باشد')
            s = serializer.save(user=request.user, order=order)
            s.order.orderStatus = '3'
            s.order.save()
            # create log
            user = request.user.username
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            os_browser = request.META['HTTP_USER_AGENT']
            createLog('Post', user, 'order/send-request/', ip, os_browser, serializer.data)
            # ----------------------------------------
            finall = Finally.objects.get(order=order, user=request.user)
            finall.confirm = '2'
            try:
                send = Send.objects.get(order=order)
            # if send does not exist
            except Send.DoesNotExist:
                sendDate = datetime.datetime.strptime(request.POST.get('sendDate'), "%Y-%m-%d").date()
                sendDate = jdatetime.datetime(sendDate.year, sendDate.month, sendDate.day)
                send = Send.objects.create(order=order, sendTime=request.POST.get('sendTime'), sendDate=sendDate)
            for item in finall.order.orderOrderitem.all():
                if item.productfield.field.confirm:
                    if item.productfield.inventory:
                        item.productfield.inventory -= item.quantity
                        item.productfield.save()
                    finall.confirm = '1'
                    serialized_data = serializer.data
                    serialized_data['confirm'] = 'نیاز به تایید فروشنده دارد'
                    confirm_list.append(item)
                    status = 'پس از تایید فروشنده به شما پیامک تایید ارسال می شود'
                else:
                    item.productfield.inventory -= item.quantity
                    item.productfield.save()
                list.append(item)
            # sms text
            if len(confirm_list):
                for i in confirm_list:
                    confirm_list2 += f'{i.productfield.field.product.name} : {i.quantity}، عدد '
            if len(confirm_list2):
                finall.order.orderStatus = '2'
                finall.order.save()
                kave_api.sms_send({
                    'receptor': finall.order.orderOrderitem.all()[0].productfield.field.seller.mobile,

                    'message': f' فروشگاه اینترنتی کالازیو \nمحصولات به شرح :[{confirm_list2}] در سبد خرید کاربر {request.user} قرار گرفته و منتظر تایید فروشنده یا از طریق لینک زیر یا پنل کاربری می باشد \n \n{settings.SITE_URI}/seller-confirm/?order={order.uuid}'

                })

            for item in list:
                if item.productfield.field.seller.sendWay:
                    finall.sendStatus = 'seller'
                    finall.sendWayOrder = ''
                    finall.order.sendPrice = 0.0
                    finall.order.save()
                else:
                    finall.sendStatus = 'kalazio'
                    finall.sendWayOrder = serializer.validated_data['sendWayOrder']
                    finall.save()
                    if finall.sendWayOrder == '2':
                        # fill send Date
                        if not request.POST.get('sendDate'):
                            return Response('روز ارسال را انتخاب کنید')
                        # fill send Time
                        if not request.POST.get('sendTime'):
                            return Response('زمان ارسال را انتخاب کنید')
                        send.sendDate = request.POST.get('sendDate')
                        send.sendTime = request.POST.get('sendTime')
                        total_weight = 0
                        for item in finall.order.orderOrderitem.all():
                            total_weight += item.productfield.field.product.weight * item.quantity
                        total_weight = int(total_weight / 7) + 1
                        finall.order.sendPrice = total_weight * 1
                        finall.order.save()
                        finall.total_price = finall.order.sendPrice + finall.order.get_total_price()
                    if finall.sendWayOrder == '1':
                        CustomerNID = finall.user.codeMelli
                        CustomerName = finall.user.first_name
                        CustomerFamily = finall.user.last_name
                        CustomerMobile = finall.user.username
                        CustomerEmail = finall.user.email
                        CustomerPostalCode = finall.address.postalCode
                        CustomerAddress = finall.address.details
                        ParcelContent = 'خرید'
                        total_weight = 0
                        ParcelValue = 0
                        for item in finall.order.orderOrderitem.all():
                            total_weight += item.productfield.field.product.weight * item.quantity
                            ParcelValue += item.productfield.get_price_after_discount_and_taxation()
                        ParcelServiceType = 1
                        DestinationCityID = finall.address.city.cityId
                        IsCollectNeed = 1
                        Weight = int(total_weight)
                        ParcelValue = ParcelValue
                        PaymentType = 1
                        NonStandardPackage = True
                        SMSService = 1
                        ShopID = 47207
                        username = 'iranian123'
                        password = '1234@#$'
                        apikey = 'D8F7F4313307EA1079BBBF954E79A48D'
                        req = requests.post(
                            f'https://ecommerceapi.post.ir/api/company/GetPrice',
                            headers={'username': username, 'password': password, 'apikey': apikey},
                            json={'ParcelServiceType': ParcelServiceType, 'DestinationCityID': DestinationCityID,
                                  'IsCollectNeed': IsCollectNeed, 'PaymentType': PaymentType, 'Weight': Weight,
                                  'ParcelValue': ParcelValue, 'NonStandardPackage': NonStandardPackage,
                                  'SMSService': SMSService, 'ShopID': ShopID})

                        add = requests.post(
                            f'https://ecommerceapi.post.ir/api/company/AddRequest',
                            headers={'username': username, 'password': password, 'apikey': apikey},
                            json={'price': {
                                'ParcelServiceType': ParcelServiceType, 'DestinationCityID': DestinationCityID,
                                'IsCollectNeed': IsCollectNeed, 'PaymentType': PaymentType, 'Weight': Weight,
                                'ParcelValue': ParcelValue, 'NonStandardPackage': NonStandardPackage,
                                'SMSService': SMSService, 'ShopID': ShopID
                            }, 'CustomerNID': CustomerNID,
                                'CustomerName': CustomerName,
                                'CustomerFamily': CustomerFamily,
                                'CustomerMobile': CustomerMobile,
                                'CustomerEmail': CustomerEmail,
                                'CustomerPostalCode': CustomerPostalCode,
                                'CustomerAddress': CustomerAddress})
                        finall.PostBarcode = add.json()['Barcode']
                        finall.save()

                        PostTrack = requests.post(
                            f'https://ecommerceapi.post.ir/api/company/GetParcelTrack?Barcode={finall.PostBarcode}',
                            headers={'username': username, 'password': password, 'apikey': apikey},
                            json={})
                        finall.PostTracking = PostTrack.json()['TotalPrice']
                        finall.order.sendPrice = req.json()['TotalPrice']
                        finall.order.save()
                        finall.save()
                    if finall.sendWayOrder == '3':
                        seller = None
                        for i in finall.order.orderOrderitem.all():
                            seller = i.seller
                        url = "https://api.alopeyk.com/api/v2/orders/price/calc"

                        payload = json.dumps({
                            "transport_type": "motor_taxi",
                            "addresses": [
                                {
                                    "type": "origin",
                                    "lat": seller.latitude if seller.latitude else 35.7173327,
                                    "lng": seller.latitude if seller.latitude else 51.42611
                                },
                                {
                                    "type": "destination",
                                    "lat": finall.address.latitude,
                                    "lng": finall.address.longitude
                                },
                            ],
                            "has_return": False,
                            "cashed": False
                        })
                        headers = {
                            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjk1OTA4OTAsImlzcyI6ImxvY2FsaG9zdDoxMzM3L2dlbmVyYXRlX3Rva2VuP2xhbmc9ZmEiLCJqdGkiOiJpMlVTZlJidW9ybmlUVFciLCJpYXQiOjE2NDUwMDU2NTUsImV4cCI6MTY3NjU0MTY1NX0.FbhNGqdNO_a33MC02hz_D2Wxb2ZmrAV3sow9hqhVpJI',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/json'
                        }

                        response = requests.request("POST", url, headers=headers, data=payload)
                        if response.json()['status'] == 'success':
                            finall.order.sendPrice = response.json()['object']['final_price']
                            finall.order.save()
                        else:
                            return Response('خطا در ارتباط با الوپیک')

                        url = "https://api.alopeyk.com/api/v2/orders"

                        payload = json.dumps({
                            "transport_type": "motor_taxi",
                            "addresses": [
                                {
                                    "type": "origin",
                                    "lat": seller.latitude if seller.latitude else 35.7173327,
                                    "lng": seller.latitude if seller.latitude else 51.42611,
                                    "person_fullname": seller.title,
                                    "person_phone": seller.mobile
                                },
                                {
                                    "type": "destination",
                                    "lat": finall.address.latitude,
                                    "lng": finall.address.longitude,
                                    "person_fullname": finall.user.first_name + ' ' + finall.user.last_name if finall.user.first_name else None,
                                    "person_phone": finall.user.username
                                },
                            ],
                            "has_return": False,
                            "cashed": False,
                            # "extra_params": "{'order_id':{finall.order.id},'customer_id':{finall.user.id}}"
                        })
                        headers = {
                            'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjE3NTc1LCJpc3MiOiJodHRwOi8vc2FuZGJveC1wYW5lbC5hbG9wZXlrLmNvbS9nZW5lcmF0ZS10b2tlbi8xNzU3NSIsImlhdCI6MTY0NTAwNjU5NSwiZXhwIjo1MjQ1MDA2NTk1LCJuYmYiOjE2NDUwMDY1OTUsImp0aSI6Im9aOVVXWWd5ejNjbDF0bzgifQ.eBoKohcJR3pig63d8FR5nCgqmL2_mEV4sC0YWekuNWM',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/json'
                        }

                        response = requests.request("POST", url, headers=headers, data=payload)

            finall.save()
            send.save()
            # if order need seller confirm
            if status:
                finall.confirm = '1'
                finall.save()
                return Response({'status': finall.order.orderStatus, 'result': serialized_data})
            return Response({'status': finall.order.orderStatus})
        return Response(serializer.errors)
    # create log
    user = request.user.username
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Post', user, 'order/send-request/', ip, os_browser)
    # ----------------------------------------
    return Response({'status': finall.order.orderStatus})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_url(request):
    # create log
    user = request.user.username
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Get', user, 'order/get-payment-url/', ip, os_browser)
    # ----------------------------------------
    order = Order.objects.filter(
        (Q(orderStatus='1') or Q(orderStatus='3') or Q(orderStatus='10')) and Q(user=request.user)).last()
    try:
        finall = Finally.objects.get(order=order)
    except Finally.DoesNotExist:
        return Response('سفارش خود را نهایی کنید قبل پرداخت', status=status.HTTP_400_BAD_REQUEST)
    finall.date = jdatetime.datetime.now()
    finall.save()
    amount = math.ceil(finall.order.get_total_price() + finall.order.sendPrice)
    MerchantId = settings.SADAD_MERCHANT_ID
    TerminalId = settings.SADAD_TERMINAL_ID
    OrderId = finall.id
    LocalDateTime = str(datetime.datetime.now())
    ReturnUrl = settings.PAYMENT_REDIRECT_URL
    SignData = encrypt_request_payment_data(TerminalId, OrderId, amount)
    UserId = int(finall.user.username)
    data = {
        'TerminalId': TerminalId,
        'MerchantId': MerchantId,
        'Amount': int(amount),
        'OrderId': OrderId,
        'LocalDateTime': LocalDateTime,
        'ReturnUrl': ReturnUrl,
        'SignData': SignData,
        'MultiplexingData': define_multiplexing_data(finall),
        'UserId': UserId,
    }
    try:
        response = requests.post(settings.SADAD_PAYMENT_REQUEST_URL, json=data,
                                 headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=5)
    except requests.Timeout:
        return Response("Bank Gateway Timeout")
    except requests.ConnectionError:
        return Response("Bank Gateway Timeout")
    ResCode = response.json()['ResCode']
    Payment_Token = response.json()['Token']
    Description = response.json()['Description']
    if int(ResCode) == 0:
        finall.pay_link = settings.SADAD_PAYMENT_URL + '?Token=' + Payment_Token
        finall.save()
        return Response({'pay_link': finall.pay_link})
    else:
        Description = Description
        return Response({'Description': Description})


# redirect url func after payment
@api_view(['GET'])
def payment_verify(request):
    try:
        final = Finally.objects.get(Q(user=request.user) and (Q(order__orderStatus='3') or Q(order__orderStatus='10')))
    # if finally does not exist
    except Finally.DoesNotExist:
        return Response('سفارش خود را نهایی کنید قبل پرداخت', status=status.HTTP_400_BAD_REQUEST)
    # create log
    user = request.user.username
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Get', user, 'order/verify/payment/', ip, os_browser)
    # ----------------------------------------
    data = {
        'Token': request.GET.get('token'),
        'SignData': encrypt_des3(request.GET.get('token')),
    }
    try:
        response = requests.post(settings.SADAD_PAYMENT_VERIFY_URL, json=data,
                                 headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=5)
    except requests.Timeout:
        return {
            'status': "fail",
            'details': {
                'Description': "زمان ارسال درخواست به پایان رسیده",
            }
        }
    except requests.ConnectionError:
        return {
            'status': "fail",
            'details': {
                'Description': "اتصال برقرار نمی باشد",
            }
        }
    ResCode = response.json()['ResCode']
    RetrivalRefNo = response.json()['RetrivalRefNo']
    SystemTraceNo = response.json()['SystemTraceNo']
    Description = response.json()['Description']
    Amount = response.json()['Amount']
    OrderId = response.json()['OrderId']
    if int(ResCode) == 0:
        final.description = response.json()['Description']
        final.RetrivalRefNo = response.json()['RetrivalRefNo']
        final.SystemTraceNo = response.json()['SystemTraceNo']
        final.pay = '1'
        final.order.orderStatus = '4'
        final.order.save()
        final.save()

        for item in final.order.orderOrderitem.all():
            item.productfield.field.sell_number += 1
            item.productfield.field.save()
        return Response({
            'status': "success",
            'details': {
                'RetrivalRefNo': RetrivalRefNo,
                'SystemTraceNo': SystemTraceNo,
                'PostTracking': final.PostTracking,
                'Amount': Amount,
                'OrderId': OrderId,
            }
        }, status=status.HTTP_200_OK)
    else:
        final.order.orderStatus = '6'
        final.order.save()
        for item in final.order.orderOrderitem.all():
            item.productfield.inventory += item.quantity
            item.productfield.save()
        return Response({
            'status': "fail",
            'details': {
                'RetrivalRefNo': RetrivalRefNo,
                'SystemTraceNo': SystemTraceNo,
                'Amount': Amount,
                'OrderId': OrderId,
                'Description': Description,
            }
        }, status=status.HTTP_400_BAD_REQUEST)


class SendPrice(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        address = None
        try:
            address = Address.objects.get(pk=self.request.GET.get('address') if self.request.GET.get('address') else 0)
        except Address.DoesNotExist:
            return Response('ادرس نامعتبر است', status=status.HTTP_400_BAD_REQUEST)
        price = {}
        order = Order.objects.filter(user=self.request.user).last()
        for item in order.orderOrderitem.all():
            if item.productfield.field.seller.payBySeller:
                return Response('price:{status: هزینه ارسال با فروشنده, amount: 0}', status=status.HTTP_200_OK)
        if self.request.GET.get('sendWayOrder') == '2':
            total_weight = 0
            for item in order.orderOrderitem.all():
                total_weight += item.productfield.field.product.weight * item.quantity
            price['status'] = 'پیک کالازیو'
            price['amount'] = total_weight * 1
        if self.request.GET.get('sendWayOrder') == '1':
            total_weight = 0
            ParcelValue = 0
            for item in order.orderOrderitem.all():
                total_weight += item.productfield.field.product.weight * item.quantity
                ParcelValue += item.productfield.get_price_after_discount_and_taxation()
            ParcelServiceType = 1
            DestinationCityID = address.city.cityId
            IsCollectNeed = 1
            Weight = int(total_weight)
            ParcelValue = ParcelValue
            PaymentType = 1
            NonStandardPackage = True
            SMSService = 1
            ShopID = 47207
            username = 'iranian123'
            password = '1234@#$'
            apikey = 'D8F7F4313307EA1079BBBF954E79A48D'
            try:
                req = requests.post(
                    f'https://ecommerceapi.post.ir/api/company/GetPrice',
                    headers={'username': username, 'password': password, 'apikey': apikey},
                    json={'ParcelServiceType': ParcelServiceType, 'DestinationCityID': DestinationCityID,
                          'IsCollectNeed': IsCollectNeed, 'PaymentType': PaymentType, 'Weight': Weight,
                          'ParcelValue': ParcelValue, 'NonStandardPackage': NonStandardPackage,
                          'SMSService': SMSService, 'ShopID': ShopID})
                price['status'] = 'پست'
                price['amount'] = req.json()['TotalPrice']
            except:
                return Response('درخواست به شرکت پست برای استعلام هزینه ارسال ناموفق بود',
                                status=status.HTTP_400_BAD_REQUEST)
        if self.request.GET.get('sendWayOrder') == '3':
            seller = None
            for i in order.orderOrderitem.all():
                seller = i.seller
            url = "https://api.alopeyk.com/api/v2/orders/price/calc"

            payload = json.dumps({
                "transport_type": "motor_taxi",
                "addresses": [
                    {
                        "type": "origin",
                        "lat": seller.latitude if seller.latitude else 35.7173327,
                        "lng": seller.latitude if seller.latitude else 51.42611
                    },
                    {
                        "type": "destination",
                        "lat": address.latitude,
                        "lng": address.longitude
                    },
                ],
                "has_return": False,
                "cashed": False
            })
            headers = {
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjk1OTA4OTAsImlzcyI6ImxvY2FsaG9zdDoxMzM3L2dlbmVyYXRlX3Rva2VuP2xhbmc9ZmEiLCJqdGkiOiJpMlVTZlJidW9ybmlUVFciLCJpYXQiOjE2NDUwMDU2NTUsImV4cCI6MTY3NjU0MTY1NX0.FbhNGqdNO_a33MC02hz_D2Wxb2ZmrAV3sow9hqhVpJI',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.json()['status'] == 'success':
                price['status'] = 'الوپیک'
                price['amount'] = response.json()['object']['final_price']
            else:
                return Response('خطا در ارتباط با الوپیک')
        return Response(f'price:{price}', status=status.HTTP_200_OK)


# state list func
class StateListView(ListAPIView):
    serializer_class = StateSerializer
    queryset = State.objects.all()


class StateCityListView(APIView):
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
        createLog('Get', user, 'order/state-city/', ip, os_browser)
        # ----------------------------------------
        state = self.request.GET.get('state')
        city = self.request.GET.get('city')
        s = None
        c = None
        if state:
            try:
                s = State.objects.get(name=state)
            # if state does not exist
            except State.DoesNotExist:
                return Response('استان یافت نشد', status=status.HTTP_400_BAD_REQUEST)

        if city:
            try:
                c = City.objects.get(name=city)
            # if city does not exist
            except City.DoesNotExist:
                return Response('شهر یافت نشد', status=status.HTTP_400_BAD_REQUEST)

        return Response({'state': s.id if s else None, 'city': c.id if c else None}, status=status.HTTP_200_OK)


# city of state
@api_view(('GET',))
def get_city(request, pk):
    # create log
    try:
        user = User.objects.get(pk=request.user.id).username
    except User.DoesNotExist:
        user = 'anonymous'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Get', user, f'order/state/{pk}', ip, os_browser)
    # ----------------------------------------
    state = State.objects.get(pk=pk)
    cities = City.objects.filter(state=state)
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Recently visited products of the user
class UserRecentVisitedProduct(ListAPIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/user-recent-visited-product/', ip, os_browser)
        # ----------------------------------------
        list = []
        visited = Visited.objects.filter(user=self.request.user)
        for visit in visited:
            # if user not visited thid product
            if visit.product not in list:
                list.append(visit.product)
        serializer = ProductSerializer(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Recently purchased user products
class UserRecentProductBuy(ListAPIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/user-recent-product-buy/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            user = User.objects.get(pk=self.request.user.id)
        # if user does not exist
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد')
        orders = Order.objects.filter(user=user, orderStatus='4')
        for order in orders:
            orderItems = OrderItem.objects.filter(order=order)
            for orderItem in orderItems:
                if orderItem.product not in list:
                    list.append(orderItem.productfield)
        serializer = ProductSerializer(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Similar products to the user's shopping cart
class RelatedCartProduct(ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        list = []
        list2 = []
        list3 = []
        list4 = []
        try:
            user = User.objects.get(pk=pk)
            userr = user.username
        # if user does not exist
        except User.DoesNotExist:
            return Response('کاربر وجود ندارد')
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'ordre/related-cart-product/{pk}', ip, os_browser)
        # ----------------------------------------
        orders = Order.objects.filter(
            Q(user=user) and (Q(orderStatus='1') or Q(orderStatus='3') or Q(orderStatus='10') or Q(orderStatus='2')))
        for order in orders:
            orderItems = OrderItem.objects.filter(order=order)
            for orderItem in orderItems:
                if orderItem.productfield not in list:
                    list.append(orderItem.productfield.field)
        for li in list:
            if li.product.category not in list2:
                list2.append(li.product.category)
        for li2 in list2:
            products = ProductField.objects.filter(product__category=li2)
            for product in products:
                if product not in list3 and product not in list:
                    list3.append(product)
        for li3 in list3:
            if li3 not in list4:
                list4.append(li3)
        serializer = ProductSerializer(list4, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# The user's future shopping cart
class NextOrderItemCreate(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = NextOrderItemSerializer(data=request.data)
        if serializer.is_valid():
            try:
                next = NextOrderItem.objects.get(user=self.request.user,
                                                 productfield=serializer.validated_data['productfield'])
            # if next order item does not exist
            except NextOrderItem.DoesNotExist:
                serializer.save(user=self.request.user)
                # create log
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = self.request.META.get('REMOTE_ADDR')
                os_browser = self.request.META['HTTP_USER_AGENT']
                createLog('Post', self.request.user.username, 'ordre/next-order-create/', ip, os_browser,
                          serializer.data)
                # ----------------------------------------
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response('محصول در سبد خرید بعدی وجود دارد')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete the user's future shopping cart
class NextOrderItemDelete(DestroyAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def delete(self, request, *args, **kwargs):
        pk = kwargs['pk']
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Delete', self.request.user.username, f'order/next-order-delete/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            productfield = ProductField.objects.get(pk=pk)
        except ProductField.DoesNotExist:
            return Response('محصول یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        try:
            next = NextOrderItem.objects.get(user=self.request.user, productfield=productfield)
        # if next order item does not exist
        except NextOrderItem.DoesNotExist:
            return Response('محصول در سبد خرید بعدی وجود ندارد')
        next.delete()
        return Response('حذف شد', status=status.HTTP_204_NO_CONTENT)


# List the user's future shopping cart
class NextOrderItemList(ListAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def get(self, *args, **kwargs):
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', self.request.user.username, 'order/next-order-list/', ip, os_browser)
        # ----------------------------------------
        next = NextOrderItem.objects.filter(user=self.request.user)
        serializer = NextOrderItemListSerializer(next, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Cancel order after payed cart
class CancelOrder(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = CancelOrderSerializer(data=request.data)
        if serializer.is_valid():
            try:
                cancel = CancelOrder.objects.get(paymentNumber=serializer.validated_data['paymentNumber'])
            except:
                try:
                    finall = Finally.objects.get(paymentNumber=serializer.validated_data['paymentNumber'])
                # if finally does not exist
                except Finally.DoesNotExist:
                    return Response('شماره پیگیری پرداخت نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
                finall.changeStatus = self.request.POST.get('changeStatus')
                order = Order.objects.get(pk=finall.order.pk)
                order.orderStatus = '8'
                order.save()
                finall.save()
                serializer.save(user=self.request.user)
                # create log
                x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = self.request.META.get('REMOTE_ADDR')
                os_browser = self.request.META['HTTP_USER_AGENT']
                createLog('Post', self.request.user.username, 'orde/cancel-order/', ip, os_browser, serializer.data)
                # ----------------------------------------
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response('سفارش در لیست مرجوعی وجود دارد', status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Date and time of sending the order for Calazio courier
class SendDateAndSendTime(APIView):
    def get(self, request, *args, **kwargs):
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', self.request.user.username, 'order/get-send-time/', ip, os_browser)
        # ----------------------------------------
        send_time = []
        now = jdatetime.datetime.now().date()
        sendDate = self.request.GET.get('sendDate')
        date_time_obj = jdatetime.datetime.strptime(sendDate, '%Y-%m-%d').date()
        # Delivery date is possible from the next 2 days to Yaad
        if date_time_obj < now + datetime.timedelta(days=2):
            return Response('تاریخ ارسال از 2 روز آینده به یعد امکان پذیر می باشد', status=status.HTTP_400_BAD_REQUEST)
        if len(Send.objects.filter(sendDate=sendDate)) and len(
                Send.objects.filter(sendDate=sendDate, sendTime='1')) < 5:
            send_time.append('9-12')
        else:
            send_time.append('')
        if len(Send.objects.filter(sendDate=sendDate)) and len(
                Send.objects.filter(sendDate=sendDate, sendTime='2')) < 5:
            send_time.append('12-15')
        else:
            send_time.append('')
        if len(Send.objects.filter(sendDate=sendDate)) and len(
                Send.objects.filter(sendDate=sendDate, sendTime='3')) < 5:
            send_time.append('15-18')
        else:
            send_time.append('')
        if len(Send.objects.filter(sendDate=sendDate)) and len(
                Send.objects.filter(sendDate=sendDate, sendTime='4')) < 5:
            send_time.append('18-21')
        else:
            send_time.append('')
        if not len(Send.objects.filter(sendDate=sendDate)):
            send_time = ['9-12', '12-15', '15-18', '18-21']
        return Response(send_time, status=status.HTTP_200_OK)


# Approval of products that need to be approved by the seller by the seller's mobile
class SellerConfirmMob(APIView):
    def post(self, *args, **kwargs):
        finall = kwargs['finall']
        user = kwargs['user']
        try:
            userr = User.objects.get(pk=user)
        # if user does not exist
        except User.DoesNotExist:
            return Response('سفارش نامعتبر می باشد', status=status.HTTP_400_BAD_REQUEST)
        try:
            final = Finally.objects.get(pk=finall, user=userr, confirm='1')
        # if finally does not exist
        except Finally.DoesNotExist:
            return Response('سفارش نامعتبر می باشد', status=status.HTTP_400_BAD_REQUEST)
        final.sellerConfirmTime = timezone.now()
        final.confirm = '2'
        final.order.orderStatus = '3'
        final.order.save()
        final.save()
        kave_api.sms_send({
            'receptor': final.user,
            'message': f' فروشگاه اینترنتی کالازیو \nسبد خرید شما توسط فروشنده : {final.order.orderOrderitem.all()[0].productfield.field.seller} تایید شد،اکنون می توانید ادامه فرایند خرید را طی کنید '
        })

        return Response('با موفقیت تایید شد', status=status.HTTP_200_OK)


# List of products in the user's shopping cart that need the seller's approval in the seller's user panel
class SellerConfirmList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        list = []
        try:
            seller = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response('شما به این صفحه دسترسی ندارید', status=status.HTTP_400_BAD_REQUEST)
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', self.request.user.username, 'order/seller-confirm-list/', ip, os_browser)
        # ----------------------------------------
        finalls = Finally.objects.filter(confirm='1', order__orderOrderitem__seller=seller.seller)
        if not len(finalls):
            return Response([], status=status.HTTP_200_OK)
        for finall in finalls:
            list.append(finall.order)
        serializer = OrderListSerializer(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Confirm the user's shopping cart for products that need to be approved by the seller using the user panel
class SellerConfirm(APIView):
    # permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication,)

    def get(self, *args, **kwargs):
        seller = None
        pk = self.request.GET.get('order')
        try:
            order = Order.objects.get(uuid=pk)
        except Order.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        try:
            finall = Finally.objects.get(order=order, confirm='1')
        # if finally does not exist
        except Finally.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        for item in finall.order.orderOrderitem.all():
            seller = item.seller
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', seller.title, f'order/seller-confirm/{self.request.GET.get("order")}', ip, os_browser)
        # ----------------------------------------
        serializer = OrderListSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, *args, **kwargs):
        seller = None
        list = []
        list2 = []
        confirm_list = ''
        uuid = None
        confirm = self.request.POST.get('confirm')
        pk = self.request.GET.get('order')
        try:
            order = Order.objects.get(uuid=pk)
        except Order.DoesNotExist:
            return Response('سفارش نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
        try:
            finall = Finally.objects.get(order=order, confirm='1')
        except Finally.DoesNotExist:
            return Response('لینک منقضی شده', status=status.HTTP_400_BAD_REQUEST)
        if finall.time > finall.time + datetime.timedelta(minutes=300):
            finall.order.orderStatus = '9'
            finall.order.save()
            return Response('زمان تایید به پایان رسیده و سفارش لفو شده است', status=status.HTTP_400_BAD_REQUEST)
        token = Token.objects.get(user=finall.user)
        deleted = []
        for item in finall.order.orderOrderitem.all():
            list.append(item)
            seller = item.seller

        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Post', seller.title, 'order/seller-confirm/', ip, os_browser,
                  {'confirm': self.request.POST.get('confirm'),
                   'inventory': self.request.POST.get(
                       'inventory') if self.request.POST.get(
                       'inventory') else None})
        # ----------------------------------------
        ###############cancel item or order when not inventory#############
        if self.request.POST.get('inventory'):
            inventory = self.request.POST.get('inventory')
            inventory = inventory.split(',')
            for i in inventory:
                for li in list:
                    if li.id == int(i):
                        for item in finall.order.orderOrderitem.all():
                            if item == li:
                                item.delete()
                                deleted.append(item.productfield.field.product)
                                finall.order.save(uuid=order.uuid)
            total_weight = 0
            for item in order.orderOrderitem.all():
                total_weight += item.productfield.field.product.weight * item.quantity
            total_weight = int(total_weight / 7) + 1
            order.sendPrice = total_weight * 1
            order.save(uuid=order.uuid)
            finall.total_price = finall.order.sendPrice + int(finall.order.get_total_price())
            finall.save()
        ###############confirm order#############
        if not confirm:
            return Response('مقدار فیلد confirm وارد نشده است', status=status.HTTP_400_BAD_REQUEST)
        if confirm == 'true' and len(finall.order.orderOrderitem.all()):
            finall.confirm = '2'
            finall.order.orderStatus = '10'
            finall.order.save()
            finall.save()
            kave_api.sms_send({
                'receptor': finall.user,
                'message': f' فروشگاه اینترنتی کالازیو \nسبد خرید شما توسط فروشنده : {finall.order.orderOrderitem.all()[0].seller}\nتایید شد،اکنون می توانید ادامه فرایند را از طریق لینک زیر طی کنید\n{settings.SITE_URI}/cart/?token={token.key} '
            })
        if confirm == 'false' and len(finall.order.orderOrderitem.all()):
            finall.order.orderStatus = '9'
            for item in finall.order.orderOrderitem.all():
                item.productfield.inventory += item.quantity
                item.productfield.save()
            finall.order.save()
            kave_api.sms_send({
                'receptor': finall.user,
                'message': f' فروشگاه اینترنتی کالازیو \nسبد خرید شما توسط فروشنده : {finall.order.orderOrderitem.all()[0].seller}\nتایید نشد و سبد خرید شما از حالت نهایی شده خارج شد،اکنون می توانید سبد خرید جدید ایجاد نمایید '
            })
            return Response('سبد خرید با موفقیت لغو شد', status=status.HTTP_200_OK)
        for i in deleted:
            confirm_list += str(i.name) + '، '
        if len(deleted) and len(finall.order.orderOrderitem.all()):
            kave_api.sms_send({
                'receptor': finall.user,
                'message': f' فروشگاه اینترنتی کالازیو \nمحصولات به شرح :{confirm_list} به علت عدم تایید فروشنده {finall.order.orderOrderitem.all()[0].seller} از سبد خرید شما حذف شده است، برای ادامه فرایند خرید سایر محصولات سبد خرید میتوانید به پنل کاربری خود مراجعه کنید '
            })
        # if not len(deleted) and len(finall.order.orderOrderitem.all()):
        #     pass
        #     kave_api.sms_send({
        #         'receptor': finall.user,
        #         'message': f' فروشگاه اینترنتی کالازیو \nسبد خرید شما توسط فروشنده : {finall.order.orderOrderitem.all()[0].seller}\nتایید شد،اکنون می توانید ادامه فرایند خرید سایر محصولات سبد خرید را طی کنید '
        #     })
        if len(deleted) and not len(finall.order.orderOrderitem.all()):
            for item in finall.order.orderOrderitem.all():
                quantity = item.quantity
                item.productfield.inventory += quantity
                item.productfield.save()
            kave_api.sms_send({
                'receptor': finall.user,
                'message': f' فروشگاه اینترنتی کالازیو \nتمام محصولات به شرح :{confirm_list} به علت عدم تایید فروشنده {finall.order.orderOrderitem.all()[0].seller} از سبد خرید شما حذف شده است، برای مشاهده میتوانید به پنل کاربری خود مراجعه کنید '
            })
        return Response('با موفقیت تایید شد', status=status.HTTP_200_OK)


# Add product to cart
@api_view(['POST', 'GET'])
def order_item(request):
    if request.method == 'POST':
        # create log
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        os_browser = request.META['HTTP_USER_AGENT']
        createLog('Post', request.user.username, 'order/order-item/', ip, os_browser,
                  {'productfield': request.POST.get('productfield'), 'quantity': request.POST.get('quantity')})
        # ----------------------------------------
        try:
            productfield = ProductFieldFeaturesValue.objects.get(pk=request.POST.get('productfield'))
        # if ProductFieldFeaturesValue does not exist
        except ProductFieldFeaturesValue.DoesNotExist:
            return Response('محصول نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
        if productfield.inventory == 0:
            return Response('موجودی محصول به پایان رسیده است', status=status.HTTP_400_BAD_REQUEST)
        if len(productfield.field.product.evidence.all()):
            u_list = []
            p_list = []
            need = []
            user_evidence = UserEvidence.objects.filter(user=request.user)
            for u_evii in user_evidence:
                u_list.append(u_evii.evidence)
            for pr_evi in productfield.field.evidence.all():
                p_list.append(pr_evi)
            for p in p_list:
                if p not in u_list:
                    need.append(p.title)
            for p in p_list:
                # needed documents for buy this product
                if p not in u_list:
                    return Response(f'مدارک لازم به شرح {need} را برای خرید این محصول ارسال کنید',
                                    status=status.HTTP_400_BAD_REQUEST)
            for u_evi in user_evidence:
                # The document you sent to purchase this product is awaiting approval
                if u_evi.evidence in productfield.field.evidence.all() and u_evi.evidenceConfirm == 'waiting':
                    return Response('مدرک ارسالی شما برای خرید این محصول در انتظار تایید می باشد',
                                    status=status.HTTP_400_BAD_REQUEST)
                if u_evi.evidence not in productfield.field.evidence.all():
                    return Response(f'مدارک لازم به شرح {need}  را برای خرید این محصول ارسال کنید ',
                                    status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(user=request.user, orderStatus='1')
        # if order does not exist
        except Order.DoesNotExist:
            order_serializer = OrderSerializer(data=request.data)
            if order_serializer.is_valid():
                request.data._mutable = True
                f = Finally.objects.filter(user=request.user).filter(
                    (Q(order__orderStatus='2') | Q(order__orderStatus='3') | Q(order__orderStatus='10')))
                # You have an unpaid order, first pay or cancel it, then create a new shopping cart
                if f:
                    return Response(
                        'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                        status=status.HTTP_400_BAD_REQUEST)
                s = order_serializer.save(user=request.user)
                order_id = 'kala-{:0>5}'.format(s.id)
                s.order_id = order_id
                s.uuid = str(uuid.uuid4())
                s.save()
                order = Order.objects.get(user=request.user, orderStatus='1')
                request.data['order'] = order.id
                OrderItem_serializer = OrderItemSerializer(data=request.data)
                seller = ProductFieldFeaturesValue.objects.get(pk=request.POST.get('productfield')).field.seller
                if OrderItem_serializer.is_valid():
                    product = productfield.field
                    finalls = None
                    if product.maxTime:
                        now = jdatetime.date.today()
                        count = 0
                        finalls = []
                        orders = Order.objects.filter(user=request.user, orderStatus='4')
                        for order in orders:
                            finall = Finally.objects.get(order=order)
                            time = finall.pay_date + datetime.timedelta(days=product.maxTime * 30)
                            if now < time:
                                finalls.append(finall)
                            for item in order.orderOrderitem.all():
                                if item.productfield.field.maxBuy and now < time:
                                    count += item.quantity
                        if count and count >= product.maxBuy:
                            return Response(
                                f'حداکثر خرید شما در {product.maxTime} ماه تعداد {product.maxBuy}میباشد که از تمام ظرفیت خرید خود برای این محصول استفاده کرده اید',
                                status=status.HTTP_400_BAD_REQUEST)
                    sum = 0
                    if finalls:
                        for finall in finalls:
                            item = OrderItem.objects.get(order=item.order)
                            field = ProductField.objects.get(pk=item.productfield.field.id)
                            if field.maxBuy:
                                sum += item.quantity
                        if product.maxBuy and int(request.POST.get('quantity')) + sum <= product.maxBuy:
                            OrderItem_serializer.save(seller=productfield.field.seller,
                                                      warranty=productfield.field.seller.warranty)
                            return Response(OrderItem_serializer.data, status=status.HTTP_201_CREATED)
                        return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
                    # Excess number of orders is allowed
                    if product.maxBuy and int(request.POST.get('quantity')) > product.maxBuy:
                        return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
                    OrderItem_serializer.save(seller=productfield.field.seller,
                                              warranty=productfield.field.seller.warranty)
                    return Response(OrderItem_serializer.data, status=status.HTTP_201_CREATED)
                return Response(OrderItem_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not order.order_id:
            order_id = f'kala-00000{order.id}'
        if not order.uuid:
            order.uuid = str(uuid.uuid1())
        order.save()
        request.data._mutable = True
        sum = 0
        try:
            f = Finally.objects.filter(order=order)
            # You have an unpaid order, first pay or cancel it, then create a new shopping cart
            if f:
                return Response(
                    'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                    status=status.HTTP_400_BAD_REQUEST)
            order_item = OrderItem.objects.get(productfield=request.POST.get('productfield'), order=order)
            completes = Order.objects.filter(user=request.user, orderStatus='4')
            # if payed order for login user
            if len(completes):
                for complete in completes:
                    finall = Finally.objects.get(order=complete)
                now = jdatetime.date.today()
                finalls = []
                if order_item.productfield.field.maxTime:
                    time = finall.pay_date + datetime.timedelta(days=order_item.productfield.field.maxTime * 30)
                else:
                    time = finall.pay_date
                if now < time:
                    finalls.append(finall)
                for finall in finalls:
                    item = OrderItem.objects.get(order=finall.order)
                    field = ProductField.objects.get(pk=item.productfield.field.id)
                    if field.maxBuy:
                        sum += item.quantity
        except OrderItem.DoesNotExist:
            request.data['order'] = order.id
            serializer = OrderItemSerializer(data=request.data)
            seller = None
            if order.orderOrderitem.first():
                seller = order.orderOrderitem.first().seller
            if serializer.is_valid():
                f = Finally.objects.filter(user=request.user, order=order, pay='2')
                # You have an unpaid order, first pay or cancel it, then create a new shopping cart
                if f:
                    return Response(
                        'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                        status=status.HTTP_400_BAD_REQUEST)
                productfield = ProductFieldFeaturesValue.objects.get(pk=request.POST.get('productfield'))
                product = productfield.field
                # Product inventory is exhausted
                if productfield.inventory == 0:
                    return Response('موجودی محصول به پایان رسیده است', status=status.HTTP_400_BAD_REQUEST)
                if len(productfield.field.product.evidence.all()):
                    u_list = []
                    p_list = []
                    need = []
                    user_evidence = UserEvidence.objects.filter(user=request.user)
                    for u_evii in user_evidence:
                        u_list.append(u_evii.evidence)
                    for pr_evi in productfield.field.evidence.all():
                        p_list.append(pr_evi)
                    for p in p_list:
                        if p not in u_list:
                            need.append(p.title)
                    for p in p_list:
                        # Necessary documents to buy the product
                        if p not in u_list:
                            return Response(f'مدارک لازم به شرح {need} را برای خرید این محصول ارسال کنید ',
                                            status=status.HTTP_400_BAD_REQUEST)
                    for u_evi in user_evidence:
                        # The document you sent to purchase this product is awaiting approval
                        if u_evi.evidence in productfield.field.evidence.all() and u_evi.evidenceConfirm == 'waiting':
                            return Response('مدرک ارسالی شما برای خرید این محصول در انتظار تایید می باشد',
                                            status=status.HTTP_400_BAD_REQUEST)
                        if u_evi.evidence not in productfield.field.evidence.all():
                            return Response(f' مدارک لازم به شرح {need} را برای خرید این محصول ارسال کنید ',
                                            status=status.HTTP_400_BAD_REQUEST)

                if len(order.orderOrderitem.all()):
                    seller2 = ProductFieldFeaturesValue.objects.get(pk=request.POST.get('productfield')).field.seller
                    # All items in the cart must be from one seller
                    if seller != seller2:
                        return Response('تمام اقلام سبد خرید باید از یک فروشنده باشد',
                                        status=status.HTTP_400_BAD_REQUEST)
                seller2 = ProductFieldFeaturesValue.objects.get(pk=request.POST.get('productfield')).field.seller
                now = jdatetime.date.today()
                count = 0
                finalls = []
                orders = Order.objects.filter(user=request.user, orderStatus='4')
                if product.maxTime:
                    for order in orders:
                        finall = Finally.objects.get(order=order)
                        time = finall.pay_date + datetime.timedelta(days=product.maxTime * 30)
                        if now < time:
                            finalls.append(finall)
                        for item in order.orderOrderitem.all():
                            if item.productfield.field.maxBuy and now < time:
                                count += item.quantity
                if product.maxBuy and count >= product.maxBuy:
                    return Response(
                        f'حداکثر خرید شما در {product.maxTime} ماه تعداد {product.maxBuy}میباشد که از تمام ظرفیت خرید خود برای این محصول استفاده کرده اید',
                        status=status.HTTP_400_BAD_REQUEST)
                if len(finalls):
                    for finall in finalls:
                        item = OrderItem.objects.get(order=finall.order)
                        field = ProductField.objects.get(pk=item.productfield.field.id)
                        if field.maxBuy:
                            sum += item.quantity
                    if product.maxBuy and int(request.POST.get('quantity')) <= product.maxBuy:
                        serializer.save(seller=seller2, user=request.user, warranty=productfield.field.seller.warranty)
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    elif product.maxBuy and int(request.POST.get('quantity')) > product.maxBuy:
                        return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
                serializer.save(seller=seller2, warranty=productfield.field.seller.warranty)
                if productfield.field.confirm:
                    st = False
                    fin = None
                    text = ''
                    try:
                        fin = Finally.objects.get(order=order)
                        st = True
                    except Finally.DoesNotExist:
                        pass
                    if st:
                        for item in fin.order.orderOrderitem.all():
                            text += str(item.productfield.field.product) + ':' + str(item.quantity) + ' عدد' + '، '
                        fin.confirm = '1'
                        fin.save()
                        kave_api.sms_send({
                            'receptor': productfield.field.seller.mobile,
                            'message': f' فروشگاه اینترنتی کالازیو \nمحصولات به شرح :[{text}] در سبد خرید کاربر {request.user}\n{settings.SITE_URI}/seller-confirm/?order={finall.id}&user={finall.user.id} قرار گرفته و منتظر تایید فروشنده یا از طریق لینک زیر یا پنل کاربری می باشد'
                        })
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if order_item.productfield.field.maxBuy == None:
            # Product inventory exceeds your purchasing capacity
            if order_item.productfield.inventory == 0 or int(
                    request.POST.get('quantity')) > order_item.productfield.inventory:
                return Response('موجودی محصول بیشتر از ظرفیت خرید شما است', status=status.HTTP_400_BAD_REQUEST)
            order_item.quantity += int(request.POST.get('quantity'))
            order_item.save()
            return Response('به تعداد محصول افزوده شد', status=status.HTTP_200_OK)
        else:
            # The number of products was increased
            if order_item.quantity + int(
                    request.POST.get('quantity')) + sum <= order_item.productfield.field.product.maxBuy:
                # Product inventory exceeds your purchasing capacity
                if order_item.productfield.inventory == 0 or int(
                        request.POST.get('quantity')) > order_item.productfield.inventory:
                    return Response('موجودی محصول بیشتر از ظرفیت خرید شما است', status=status.HTTP_400_BAD_REQUEST)
                order_item.quantity += int(request.POST.get('quantity'))
                order_item.save()
                return Response('به تعداد محصول افزوده شد', status=status.HTTP_200_OK)
            return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        try:
            userr = User.objects.get(pk=request.user.id).username
        except User.DoesNotExist:
            return Response('کاربر موجود نیست یا لاگین نشده است')
        order = Order.objects.filter(user=request.user).filter(
            (Q(orderStatus='1') | Q(orderStatus='3') | Q(orderStatus='2') | Q(orderStatus='6') | Q(
                orderStatus='10'))).first()
        # if order does not exist
        if not order:
            return Response('سفارش وجود ندارد')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        os_browser = request.META['HTTP_USER_AGENT']
        createLog('Get', userr, 'order/order-item/', ip, os_browser)
        # ----------------------------------------
        query = order.orderOrderitem.all()
        serializer = OrderListSerializer(order)
        return Response(serializer.data)


# Use gift cards to order
class AddGiftToOrder(APIView):
    permission_classes(IsAuthenticated, )

    def post(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Post', userr, 'order/add-gift-order/', ip, os_browser,
                  {'serial': self.request.POST.get('serial'), 'order': self.request.POST.get('order')})
        # ----------------------------------------
        serializer = GiftSerializerForOrder(data=self.request.data)
        if serializer.is_valid():
            try:
                gift = Gift.objects.get(serial=serializer.validated_data['serial'], use=False)
            # if gift does not exist
            except Gift.DoesNotExist:
                return Response('کارت هدیه نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
            try:
                order = Order.objects.get(id=self.request.POST.get('order'))
            # if order does not exist
            except Order.DoesNotExist:
                return Response('سفارش نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
            price = order.get_total_price()
            # The amount of the gift card must be less than the total amount of the order
            if gift.amount > price:
                return Response('مبلغ کارت هدیه بایستی از مبلغ کل سفارش کمتر باشد', status=status.HTTP_400_BAD_REQUEST)
            order.gift = gift
            order.get_total_price = order.get_total_price() - gift.amount
            order.save()
            gift.orderCode = order
            gift.use = True
            gift.save()
            return Response('کد تخفیف اعمال شد', status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Order modes for a user
class OrderView(APIView, StandardResultsSetPagination):
    permission_classes(IsAuthenticated, )

    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, 'order/', ip, os_browser)
        # ----------------------------------------
        objects = Finally.objects.filter(user=self.request.user)
        if objects:
            for object in objects:
                time = object.time + datetime.timedelta(minutes=300)
                now1 = timezone.now()
                if (object.order.orderStatus == '3' or object.order.orderStatus == '10') and now1 > time:
                    object.order.orderStatus = '7'
                    object.order.save()
                if object.order.orderStatus == '2' and now1 > time:
                    object.order.orderStatus = '9'
                    object.order.save()

        if not self.request.GET.get('status'):
            raise ValidationError('پارامتر وضعیت سفارش وارد نشده است')
        status = self.request.GET.get('status')
        if status == '1' or status == '2' or status == '3' or status == '4' or status == '5' or status == '6' or status == '7' or status == '8' or status == '9' or status == '10' or status == '11':
            query = Order.objects.filter(user=self.request.user, orderStatus=status).order_by('-id')
            res = query
        elif status == '0':
            query = Order.objects.filter(user=self.request.user).order_by('-id')
            res = query
        else:
            return Response('سفارش نا معتبر می باشد')
        result_page = self.paginate_queryset(res, self.request, view=self)
        serializer = OrderSerializerForOrders(result_page, many=True)
        return self.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def count_order(request):
    count = {}
    count['1'] = Order.objects.filter(
        Q(user=request.user) & (Q(orderStatus=1) | Q(orderStatus=3) | Q(orderStatus=10))).count()
    count['2'] = Order.objects.filter(
        Q(user=request.user) & (Q(orderStatus=2) | Q(orderStatus=4) | Q(orderStatus=5))).count()
    count['3'] = Order.objects.filter(user=request.user, orderStatus=11).count()
    count['4'] = Order.objects.filter(user=request.user, orderStatus=8).count()
    count['5'] = Order.objects.filter(
        Q(user=request.user) & (Q(orderStatus=6) | Q(orderStatus=7) | Q(orderStatus=9))).count()
    return Response(count, status=status.HTTP_200_OK)


# Get detail of a order
class OrderViewDetail(ListAPIView):
    serializer_class = OrderSerializerForOrders
    permission_classes(IsAuthenticated, )

    def get_queryset(self):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/detail/{self.kwargs["id"]}', ip, os_browser)
        # ----------------------------------------
        return Order.objects.filter(user=self.request.user, id=self.kwargs['id'])


# Get factor of a payed order
class Factor(RetrieveAPIView):
    serializer_class = OrderSerializerForOrders
    permission_classes(IsAuthenticated, )

    def get_queryset(self):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/factor/{self.kwargs["pk"]}', ip, os_browser)
        # ----------------------------------------
        return Order.objects.all()


# Get failed order of a user
class FailOrders(ListAPIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, 'order/fail-orders/', ip, os_browser)
        # ----------------------------------------
        try:
            order = Order.objects.get(user=self.request.user, orderStatus='6')
        # if order does not exist
        except Order.DoesNotExist:
            return Response('سفارش وجود ندارد')
        order_items = OrderItem.objects.filter(order=order)
        serializer = OrderItemListSerializer(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Cancel a failed order of user
class CancelFailOrder(DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/cancel-fail-orders/{self.kwargs["pk"]}', ip, os_browser)
        # ----------------------------------------
        queryset = Finally.objects.filter(user=self.request.user, orderStatus='6', id=self.kwargs['pk'])
        return queryset


# Cancel finally order
class CancelFinallyOrder(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Delete', userr, 'order/cancel-finally-orders/', ip, os_browser)
        # ----------------------------------------
        try:
            queryset = Finally.objects.get(Q(user=self.request.user) & (
                    Q(order__orderStatus=2) | Q(order__orderStatus=3) | Q(order__orderStatus=10)))
        # if finally does not exist
        except Finally.DoesNotExist:
            return Response('سفارش ثبت شده ندارید', status=status.HTTP_400_BAD_REQUEST)
        queryset.order.orderStatus = '7'
        queryset.order.save()
        return Response('با موفقیت پاک شد', status=status.HTTP_204_NO_CONTENT)


# Get , update, delete addresses of user
class RetrieveAddress(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/retreive-address/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            address = Address.objects.get(pk=pk)
        # if address does not exist
        except Address.DoesNotExist:
            return Response('ادرس وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        serializer = AddressSerializerRet(address)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            address = Address.objects.get(pk=pk)
        # if address does not exist
        except Address.DoesNotExist:
            return Response('ادرس وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        serializer = AddressSerializerRetForEdit(instance=address, data=self.request.data)
        if serializer.is_valid():
            try:
                state = State.objects.get(name=self.request.POST.get('state'))
            except State.DoesNotExist:
                return Response('استان نامعتبر است', status=status.HTTP_400_BAD_REQUEST)
            try:
                city = City.objects.filter(name=self.request.POST.get('city')).first()
            except City.DoesNotExist:
                return Response('شهر نامعتبر است', status=status.HTTP_400_BAD_REQUEST)
            s = serializer.save(user=self.request.user)
            s.city = city
            s.state = state
            s.save()
            # create log
            try:
                userr = User.objects.get(pk=self.request.user.id).username
            except User.DoesNotExist:
                userr = 'anonymous'
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            os_browser = self.request.META['HTTP_USER_AGENT']
            createLog('Put', userr, f'order/retreive-address/{pk}', ip, os_browser, serializer.data)
            # ----------------------------------------
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        pk = kwargs['pk']
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Delete', userr, f'order/retreive-address/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            address = Address.objects.get(pk=pk)
        # if address does not exist
        except Address.DoesNotExist:
            return Response('ادرس وجود ندارد', status=status.HTTP_400_BAD_REQUEST)
        address.delete()
        return Response('با موفقیت پاک شد', status=status.HTTP_200_OK)


# Get all address of user
class GetAllAddress(ListAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)
    pagination_class = None
    serializer_class = AddressSerializerRet

    def get_queryset(self):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/get-all-address/', ip, os_browser)
        # ----------------------------------------
        return Address.objects.filter(user=self.request.user)


# Create address for user
class CreateAddress(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            # create log
            try:
                userr = User.objects.get(pk=self.request.user.id).username
            except User.DoesNotExist:
                userr = 'anonymous'
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            os_browser = self.request.META['HTTP_USER_AGENT']
            createLog('Post', userr, 'order/create-address/', ip, os_browser,
                      {'state': request.POST.get('state'), 'city': request.POST.get('city'),
                       'postalCode': request.POST.get('postalCode'), 'details': request.POST.get('details'),
                       'plaque': request.POST.get('plaque'),
                       'floor': request.POST.get('floor') if request.POST.get('floor') else None,
                       'nighbourhood': request.POST.get('nighbourhood') if request.POST.get(
                           'nighbourhood') else None, 'longitude': request.POST.get('longitude'),
                       'latitude': request.POST.get('latitude'),
                       'firstname': request.POST.get('firstname') if request.POST.get(
                           'forMe') == 'false' else self.request.user.first_name,
                       'lastname': request.POST.get('lastname') if request.POST.get(
                           'forMe') == 'false' else self.request.user.last_name,
                       'phone': request.POST.get('phone') if request.POST.get(
                           'forMe') == 'false' else self.request.user.username})
            # ----------------------------------------
            ss = request.POST.get('state')
            cc = request.POST.get('city')
            try:
                s = State.objects.get(name=ss)
            # if state does not exist
            except State.DoesNotExist:
                return Response('استان نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
            try:
                c = City.objects.get(name=cc, state=s)
            # if city does not exist
            except City.DoesNotExist:
                return Response('شهر نا معتبر است', status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data['forMe']:
                serializer.save(user=self.request.user, firstname=self.request.user.first_name,
                                lastname=self.request.user.last_name, phone=self.request.user, state=s, city=c)
            else:
                try:
                    if serializer.validated_data['firstname'] == '':
                        return Response('نام باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                # enter firstname
                except:
                    return Response('نام باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                try:
                    if serializer.validated_data['lastname'] == '':
                        return Response('نام خانوادگی باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                # enter lastname
                except:
                    return Response('نام خانوادگی باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                try:
                    if serializer.validated_data['phone'] == '':
                        return Response('تلفن باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                # enter phone
                except:
                    return Response('تلفن باید وارد شود', status=status.HTTP_400_BAD_REQUEST)
                serializer.save(user=self.request.user, state=s, city=c)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get payed order
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_complete_order(request):
    if request.method == 'GET':
        # create log
        try:
            userr = User.objects.get(pk=request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        os_browser = request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/get-complete-order/', ip, os_browser)
        # ----------------------------------------
        query = Order.objects.filter(
            Q(user=request.user) and (Q(orderStatus='4') | Q(orderStatus='5') | Q(orderStatus='11')))
        serializer = GetCompleteOrderSerializer(query, many=True, context={'host': request._current_scheme_host})
        return Response(serializer.data)


# Get current finally order
class CurrentFinally(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(uuid=self.request.GET.get('order'))
        except Order.DoesNotExist:
            return Response('سفارش نامعتبر است', status=status.HTTP_400_BAD_REQUEST)
        # create log
        try:
            userr = User.objects.get(pk=order.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/current-finally/', ip, os_browser)
        # ----------------------------------------
        try:
            fin = Finally.objects.get(
                Q(user=order.user) & (
                        Q(order__orderStatus='3') | Q(order__orderStatus='2') | Q(order__orderStatus='10')))
        # if finally does not exist
        except Finally.DoesNotExist:
            return Response('سفارش موجود نمی باشد', status=status.HTTP_400_BAD_REQUEST)
        st = None
        if fin.order.orderStatus == '3':
            st = 'در انتظار پرداخت'
        # Awaiting seller approval
        if fin.order.orderStatus == '2':
            st = 'در انتظار تایید فروشنده'
        if fin.order.orderStatus == '10':
            st = 'تایید توسط فروشنده و در انتظار پرداخت'
        serializer = FinallySerializerForList(fin)
        return Response({'data': serializer.data, 'status': st, 'pay_link': fin.pay_link}, status=status.HTTP_200_OK)


# Delete item from current cart
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def order_item_delete(request, pk):
    # create log
    try:
        userr = User.objects.get(pk=request.user.id).username
    except User.DoesNotExist:
        userr = 'anonymous'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    os_browser = request.META['HTTP_USER_AGENT']
    createLog('Delete', userr, f'order/order-item-delete/{pk}', ip, os_browser)
    # ----------------------------------------
    try:
        order = Order.objects.get(user=request.user, orderStatus='1')
    # if order does not exist
    except Order.DoesNotExist:
        return Response('سفارش وجود ندارد')
    # This product was removed from the cart
    if request.method == 'DELETE':
        finall = Finally.objects.filter(
            Q(user=request.user) and (
                    Q(order__orderStatus='2') | Q(order__orderStatus='3') | Q(order__orderStatus='10')))
        # You have an unpaid order, first pay or cancel it, then create a new shopping cart
        if finall:
            return Response(
                'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                status=status.HTTP_400_BAD_REQUEST)
        for item in order.orderOrderitem.all():
            if item.productfield.id == pk:
                item.delete()
        if not len(order.orderOrderitem.all()):
            order.delete()
        return Response('این محصول از سبد خرید حذف شد', status=status.HTTP_204_NO_CONTENT)


# Increase item in current cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_item_inc(request):
    if request.method == 'POST':
        # create log
        try:
            userr = User.objects.get(pk=request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        os_browser = request.META['HTTP_USER_AGENT']
        createLog('Post', userr, f'order/order-item-inc/', ip, os_browser,
                  {'productfield': request.data.get('productfield')})
        # ----------------------------------------
        try:
            order = Order.objects.get(user=request.user, orderStatus='1')
        # if order does not exist
        except Order.DoesNotExist:
            return Response('سفارشی وجود ندارد', status=status.HTTP_404_NOT_FOUND)
        try:
            order_item = order.orderOrderitem.get(productfield=request.data.get('productfield'))
        # if order item does not exist
        except OrderItem.DoesNotExist:
            return Response('این محصول در سبد خرید شما وجود ندارد', status=status.HTTP_404_NOT_FOUND)
        # The stock of this product has run out
        if order_item.productfield.inventory == 0:
            return Response('موجودی این محصول به پایان رسیده است', status=status.HTTP_404_NOT_FOUND)
        sum = 0
        if order_item.productfield.field.maxTime:
            completes = Order.objects.filter(user=request.user, orderStatus='4')
            finall = None
            if completes:
                for complete in completes:
                    finall = Finally.objects.get(order=complete)
                now = jdatetime.date.today()
                finalls = []
                time = finall.pay_date + datetime.timedelta(days=order_item.productfield.field.maxTime * 30)
                if now < time:
                    finalls.append(finall)
                for finall in finalls:
                    item = OrderItem.objects.get(order=finall.order)
                    field = ProductField.objects.get(pk=item.productfield.field.id)
                    if field.maxBuy:
                        sum += item.quantity
        # The number of orders for this product was increased
        if order_item:
            finall = Finally.objects.filter(
                Q(user=request.user) and (
                        Q(order__orderStatus='2') | Q(order__orderStatus='3') | Q(order__orderStatus='10')))
            if finall:
                return Response(
                    'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                    status=status.HTTP_400_BAD_REQUEST)
            # Excess number of orders is allowed
            if order_item.productfield.field.maxBuy and sum + order_item.quantity + 1 > order_item.productfield.field.maxBuy:
                return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
            order_item.quantity += 1
            order_item.save()
            order.save()
            serializer = OrderItemListSerializerForOrderList(
                OrderItem.objects.get(order=order, productfield=request.data.get('productfield')))
            return Response({'text': 'به تعداد سفارش این محصول افزوده شد', 'data': serializer.data},
                            status=status.HTTP_200_OK)
        return Response('تعداد سفارش بیش از حد مجاز است', status=status.HTTP_400_BAD_REQUEST)
    return HttpResponse()


# Decrease item in current cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_item_dec(request):
    if request.method == 'POST':
        # create log
        try:
            userr = User.objects.get(pk=request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        os_browser = request.META['HTTP_USER_AGENT']
        createLog('Post', userr, f'order/order-item-dec/', ip, os_browser,
                  {'productfield': request.data.get('productfield')})
        # ----------------------------------------
        try:
            order = Order.objects.get(user=request.user, orderStatus='1')
        # if order does not exist
        except:
            return Response('سفارشی وجود ندارد', status=status.HTTP_404_NOT_FOUND)
        try:
            order_item = order.orderOrderitem.get(productfield=request.data.get('productfield'))
        # if order item does not exist
        except:
            return Response('محصول وجود ندارد', status=status.HTTP_404_NOT_FOUND)
        finall = Finally.objects.filter(
            Q(user=request.user) and (
                    Q(order__orderStatus='2') | Q(order__orderStatus='3') | Q(order__orderStatus='10')))
        # You have an unpaid order, first pay or cancel it, then create a new shopping cart
        if finall:
            return Response(
                'شما سفارش پرداخت نشده دارید ابتدا ان را پرداخت یا لغو کنید سپس سبد خرید جدید ایجاد کنید ',
                status=status.HTTP_400_BAD_REQUEST)
        # This product was removed from the cart
        if order_item.quantity == 1:
            order_item.delete()
            if not len(order.orderOrderitem.all()):
                order.delete()
            return Response('این محصول از سبد خرید حذف شد', status=status.HTTP_200_OK)
        order_item.quantity -= 1
        order_item.save()
        serializer = OrderItemListSerializerForOrderList(
            OrderItem.objects.get(order=order, productfield=request.data.get('productfield')))
        return Response({'text': 'از تعداد سفارش این محصول کاسته شد', 'data': serializer.data},
                        status=status.HTTP_200_OK)


# Get report of orders
class OrdersReport(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/orders-report/', ip, os_browser)
        # ----------------------------------------
        finals = Finally.objects.all()
        filter = self.request.GET.get('filter')

        # Filter by order paye date
        if filter == 'date':
            list = []
            if self.request.GET.get('start') and self.request.GET.get('end'):
                start = parser.parse(self.request.GET.get('start')).date()
                end = parser.parse(self.request.GET.get('end')).date()
                for final in finals:
                    time = jdatetime.date.fromgregorian(year=final.date.year, month=final.date.month,
                                                        day=final.date.day)
                    if start < time < end:
                        list.append(final)
                    serializer = FinallySerializerForList(list, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the start and end dates
            else:
                return Response('تاریخ شروع و پایان را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)
        # Filter by seller
        if filter == 'seller':
            list = []
            if self.request.GET.get('name'):
                for final in finals:
                    for item in final.order.orderOrderitem.all():
                        if self.request.GET.get('name') == item.seller.title:
                            list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the name of the seller
            else:
                return Response('نام فروشنده را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by product
        if filter == 'product':
            list = []
            if self.request.GET.get('code'):
                for final in finals:
                    for item in final.order.orderOrderitem.all():
                        if int(self.request.GET.get('code')) == item.productfield.id:
                            list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            if self.request.GET.get('name'):
                for final in finals:
                    for item in final.order.orderOrderitem.all():
                        if self.request.GET.get('name') == item.productfield.product.name:
                            list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the product code or name
            else:
                return Response('کد یا نام محصول را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by order
        if filter == 'order':
            list = []
            if self.request.GET.get('code'):
                for final in finals:
                    if int(self.request.GET.get('code')) == final.order.id:
                        list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the order code
            else:
                return Response('کد سفارش را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by user mobile
        if filter == 'mobile':
            list = []
            if self.request.GET.get('phone'):
                for final in finals:
                    if self.request.GET.get('phone') == final.user.username:
                        list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the phone number
            else:
                return Response('شماره تلفن را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by retrival ref number
        if filter == 'retrival':
            list = []
            if self.request.GET.get('code'):
                for final in finals:
                    if self.request.GET.get('code') == final.RetrivalRefNo:
                        list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the tracking code
            else:
                return Response('کد پیگیری را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by order sent today
        if filter == 'today':
            list = []
            for final in finals:
                time = jdatetime.date.fromgregorian(year=final.sellerConfirmTime.year,
                                                    month=final.sellerConfirmTime.month,
                                                    day=final.sellerConfirmTime.day)
                if time.year == jdatetime.datetime.today().year and time.month == jdatetime.datetime.today().month and time.day == jdatetime.datetime.today().day:
                    list.append(final)
            serializer = FinallySerializerForList(list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Filter by order sent tomorrow
        if filter == 'tomorrow':
            list = []
            for final in finals:
                time = jdatetime.date.fromgregorian(year=final.sellerConfirmTime.year,
                                                    month=final.sellerConfirmTime.month,
                                                    day=final.sellerConfirmTime.day)
                if time.year == jdatetime.datetime.today().year and time.month == jdatetime.datetime.today().month and time.day == (
                        (
                                jdatetime.datetime.today() + jdatetime.timedelta(days=1)).day):
                    list.append(final)
            serializer = FinallySerializerForList(list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Filter by order sent in future
        if filter == 'future':
            list = []
            for final in finals:
                time = jdatetime.date.fromgregorian(year=final.sellerConfirmTime.year,
                                                    month=final.sellerConfirmTime.month,
                                                    day=final.sellerConfirmTime.day)
                if time.year == jdatetime.datetime.today().year and time.month == jdatetime.datetime.today().month and time.day == (
                        (
                                jdatetime.datetime.today() + jdatetime.timedelta(days=2)).day):
                    list.append(final)
            serializer = FinallySerializerForList(list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Filter by brand
        if filter == 'brand':
            list = []
            if self.request.GET.get('name'):
                for final in finals:
                    for item in final.order.orderOrderitem.all():
                        if self.request.GET.get('name') == item.productfield.product.brand.name:
                            list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the brand name
            else:
                return Response('نام برند را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Filter by order status
        if filter == 'status':
            list = []
            if self.request.GET.get('status'):
                for final in finals:
                    if self.request.GET.get('status') == final.order.orderStatus:
                        list.append(final)
                serializer = FinallySerializerForList(list, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the status of the order
            else:
                return Response('وضعیت سفارش را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)
        # Enter the search filter
        if not filter or filter == '':
            return Response('فیلتر جستجو را وارد کنید', status=status.HTTP_400_BAD_REQUEST)


# Get report of a order
class OrderReport(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, *args, **kwargs):
        pk = self.request.GET.get('pk')
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/order-report/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            order = Order.objects.get(id=int(pk))
        # if order does not exist
        except Order.DoesNotExist:
            return Response('سفارش مورد نظر یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        filter = self.request.GET.get('filter')

        # Filter by product
        if filter == 'products':
            list = []
            for item in order.orderOrderitem.all():
                list.append(item.productfield)
            serializer = ProductSerializer(list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Filter by category
        if filter == 'category':
            list = []
            for item in order.orderOrderitem.all():
                list.append({'product': item.productfield.product.name, 'category': item.productfield.get_category()})
            return Response(list)

        # Filter by product name
        if filter == 'product':
            if self.request.GET.get('name'):
                for item in order.orderOrderitem.all():
                    if self.request.GET.get('name') == item.productfield.product.name:
                        serializer = ProductSerializer(item.productfield)
                        return Response(serializer.data, status=status.HTTP_200_OK)
            # Specify the product name
            else:
                return Response('نام محصول را مشخص کنید', status=status.HTTP_400_BAD_REQUEST)

        # Get items in order
        if filter == 'order-item':
            list = []
            for item in order.orderOrderitem.all():
                list.append(item.id)
            return Response(list)

        # Get brands of product in order
        if filter == 'brand':
            list = []
            for item in order.orderOrderitem.all():
                list.append({'product': item.productfield.product.name, 'brand': item.productfield.product.brand.name})
            return Response(list)

        # Get pay date of order
        if filter == 'pay-date':
            try:
                final = Finally.objects.get(order=order)
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            return Response(str(final.date))

        # Get send date of order
        if filter == 'send-date':
            try:
                final = Finally.objects.get(order=order)
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            return Response(str(final.sellerConfirmTime))

        # Get retrival ref number of order
        if filter == 'retrival':
            try:
                final = Finally.objects.get(order=order)
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            return Response(final.RetrivalRefNo)

        # Get total price of order
        if filter == 'order-price':
            sum = 0
            for item in order.orderOrderitem.all():
                sum = item.productfield.get_price_after_discount_and_taxation() * item.quantity
            return Response(sum + order.sendPrice)

        # Get status of order
        if filter == 'status':
            return Response(order.get_orderStatus())

        # Get post address of order
        if filter == 'post-add':
            try:
                final = Finally.objects.get(order=order)
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            return Response(final.address.details)

        # Get postal code of order
        if filter == 'post-code':
            try:
                final = Finally.objects.get(order=order)
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            return Response(final.address.postalCode)

        # Get user identify of order
        if filter == 'user-identify':
            return Response(order.user.get_authorized())

        # Get send ducument for order
        if filter == 'documents':
            list = []
            result = []
            for item in order.orderOrderitem.all():
                list.append(item.productfield)
            for li in list:
                for l in li.evidence.all():
                    u_ev = UserEvidence.objects.filter(evidence=l.id, user__id=order.user.id)
                    for e in u_ev:
                        if e:
                            result.append({'product': li.product.name, 'document-name': l.title,
                                           'file': e.get_absolute_file(),
                                           'confirm': e.get_evidenceConfirm()})
            return Response(result)

        # Get buyer info of order
        if filter == 'buyer':
            try:
                final = Finally.objects.get(order=order, pay='1')
            # if finally does not exist
            except Finally.DoesNotExist:
                return Response(None)
            if final.address.forMe:
                return Response({
                    'fullname': final.user.first_name + ' ' + final.user.last_name,
                    'post-add': final.address.details,
                    'post-code': final.address.postalCode,
                    'melli-code': final.user.codeMelli,
                    'phone': final.user.phone,
                    'mobile': final.user.username
                })
            else:
                return Response({
                    'fullname': final.address.firstname + ' ' + final.address.lastname,
                    'post-add': final.address.details,
                    'post-code': final.address.postalCode,
                    'melli-code': final.user.codeMelli,
                    'phone': '',
                    'mobile': final.address.phone
                })

        # Get seller info of order
        if filter == 'seller':
            seller = None
            for item in order.orderOrderitem.all():
                seller = item.seller
            return Response({
                'title': seller.title,
                'code': seller.code,
                'registrationId': seller.registrationId,
                'melliId': seller.melliId,
                'phone': seller.phone,
                'mobile': seller.mobile,
                'state': seller.state.name,
                'city': seller.city.name,
                'address': seller.address
            })

        # Get product info of order
        if filter == 'products-details':
            list = []
            result = []
            for item in order.orderOrderitem.all():
                list.append({'product': item.productfield, 'quantity': item.quantity})
            for li in list:
                result.append({
                    'title': li['product'].product.name,
                    'product_id': li['product'].product.id,
                    'productfield_id': li['product'].id,
                    'summery': li['product'].product.summary,
                    'quantity': li['quantity'],
                    'price': li['product'].get_price_after_discount(),
                    'total_price': li['product'].get_price_after_discount() * li['quantity'],
                    'offer': (li['product'].productfield.get_price() - li['product'].get_price_after_discount())
                             * item.quantity,
                    'tax': (li['product'].get_price_after_discount_and_taxation()
                            - li['product'].get_price_after_discount()) * item.quantity,
                    'final_price': li['product'].get_price_after_discount_and_taxation() * item.quantity
                })
            return Response(result)

        # Get order details of order
        if filter == 'order-details':
            try:
                final = Finally.objects.get(order=order)
            except Finally.DoesNotExist:
                return Response(None)
            return Response({
                'send-price': final.order.sendPrice,
                'send-method': final.get_sendWayOrder(),
                'total-price': final.order.get_total_price(),
                'send-date': final.sellerConfirmTime,
                'order-id': final.order.id,
                'RetrivalRefNo': final.RetrivalRefNo,
                'SystemTraceNo': final.SystemTraceNo
            })


# Get all state for update database
class PostState(APIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/post-state-list/', ip, os_browser)
        # ----------------------------------------
        username = 'iranian123'
        password = '1234@#$'
        apikey = 'D8F7F4313307EA1079BBBF954E79A48D'
        req = requests.post(
            f'https://ecommerceapi.post.ir/api/company/GetStates',
            headers={'username': username, 'password': password, 'apikey': apikey})
        for res in req.json():
            try:
                st = State.objects.get(name=res['StateName'])
                st.stateId = res['StateID']
                st.save()
            # if state does not exist
            except State.DoesNotExist:
                State.objects.create(name=res['StateName'], stateId=res['StateID'])

        return Response(req.json(), status=status.HTTP_200_OK)


# Get all cities for update database
class PostCity(APIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/post-city-list/', ip, os_browser)
        # ----------------------------------------
        username = 'iranian123'
        password = '1234@#$'
        apikey = 'D8F7F4313307EA1079BBBF954E79A48D'
        req = requests.post(
            f'https://ecommerceapi.post.ir/api/company/GetStates',
            headers={'username': username, 'password': password, 'apikey': apikey})
        for res in req.json():
            st = State.objects.get(name=res['StateName'])
            cities = requests.post(
                f'https://ecommerceapi.post.ir/api/company/GetStateCities?stateid={res["StateID"]}',
                headers={'username': username, 'password': password, 'apikey': apikey})
            for city in cities.json():
                try:
                    ct = City.objects.get(name=city['CityName'], state__stateId=st.stateId)
                    ct.cityId = city['CityID']
                    ct.save()
                # if city does not exist
                except City.DoesNotExist:
                    City.objects.create(name=city['CityName'], cityId=city['CityID'], state=st)
        return Response(req.json(), status=status.HTTP_200_OK)


# Get cities of a state
class PostCityList(APIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/post-city/', ip, os_browser)
        # ----------------------------------------
        try:
            st = State.objects.get(stateId=self.request.GET.get("stateid"))
            cities = City.objects.filter(state=st)
            serializer = CitySerializer(cities, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # if state does not exist
        except State.DoesNotExist:
            return Response('ایدی استان نامعتبر است', status=status.HTTP_400_BAD_REQUEST)


# Get all state
class PostStateList(APIView):
    def get(self, *args, **kwargs):
        # create log
        try:
            userr = User.objects.get(pk=self.request.user.id).username
        except User.DoesNotExist:
            userr = 'anonymous'
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'order/post-state/', ip, os_browser)
        # ----------------------------------------
        serializer = StateSerializer(State.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
