import requests
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from Kalazio import settings
from log.views import createLog
from user.models import User
from .serializers import BrandSerializer, BannerSerializer
from .models import Brand, Banner
from product.models import Product, ProductField
from product.serializers import ProductSerializer, ProductSerializerForAllProduct, ProductSerializerForRelated
from Kalazio.pagination import StandardResultsSetPagination


# Create your views here.


# Get detail of each brand
class DetailOfBrand(RetrieveAPIView):
    serializer_class = BrandSerializer
    pagination_class = None

    def get_queryset(self):
        pk = self.kwargs['pk']
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
        createLog('Get', user, f'brands/{pk}/', ip, os_browser)
        # ----------------------------------------
        return Brand.objects.filter(pk=pk)


# Most visited products of any brand
class MoreVisitProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')

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
        createLog('Get', user, f'brands/visited-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------
        products = Product.objects.filter(brand=brand).order_by('-visit')
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Best-selling products of any brand
class MoreSellNumberProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        list = []
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')

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
        createLog('Get', user, f'brands/bestsellers-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------

        products = ProductField.objects.all().order_by('-sell_number')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, brand=brand)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Popular products of any brand
class MoreLikeProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')
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
        createLog('Get', user, f'brands/liked-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------

        products = Product.objects.filter(brand=brand).order_by('-like_number')
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForRelated(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Latest products of any brand
class LatestProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')
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
        createLog('Get', user, f'brands/latest-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------

        products = Product.objects.filter(brand=brand).order_by('-id')
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForRelated(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Inexpensive products of any brand
class InExpensiveProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        list = []
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')
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
        createLog('Get', user, f'brands/inexpensive-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------

        products = ProductField.objects.all().order_by('price')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, brand=brand)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Expensive products of any brand
class ExpensiveProductOfBrand(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        pk = kwargs['pk']
        list = []
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response('برند موجود نمی باشد')
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
        createLog('Get', user, f'brands/expensive-product-brand/{pk}/', ip, os_browser)
        # ----------------------------------------

        products = ProductField.objects.all().order_by('-price')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, brand=brand)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Get all brand
class AllBrand(ListAPIView):
    serializer_class = BrandSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
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
        createLog('Get', user, 'brands/all-brand/', ip, os_browser)
        # ----------------------------------------
        return Brand.objects.all()


# Get all banner
class AllBanner(APIView):
    pagination_class = StandardResultsSetPagination

    def get(self, *args, **kwargs):
        type = self.request.GET.get('type')
        query = Banner.objects.filter(type=type)
        serializer = BannerSerializer(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
