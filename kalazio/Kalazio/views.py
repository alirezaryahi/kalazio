import random
from itertools import islice

import numpy
from rest_framework.views import APIView
import numpy as np
from Kalazio.pagination import StandardResultsSetPagination
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from brand.models import Brand, ImageBanner, VideoBanner
from brand.serializers import BrandSerializerForImageBanner, BrandSerializerForList, BrandSerializer, \
    ImageBannerSerializerForGet, VideoBannerSerializerForGet
from log.views import createLog
from order.models import Order
from .pagination import StandardResultsSetPagination
from product.models import Product, Category, Visited, ProductField, Seller, ProductFieldFeaturesValue
from product.serializers import ProductSerializerForListDiscountPrice, ProductSerializerForList, CategorySerializer, \
    SubCategorySerializer, ProductSerializer, VisitedProductSerializer, CategorySerializerForSearchInCategory, \
    SellerSerializer, ProductSerializerForAllProduct, ProductSerializerForRelated, ProductSerializerForSearch
from user.models import User
import operator
from django.db.models import Q


# Main search

class SearchData(APIView):
    def get(self, request, *args, **kwargs):
        seller_list = []
        sellers = Seller.objects.all()
        for seller in sellers:
            seller_list.append({
                'id': seller.id,
                'name': seller.title
            })

        brand_list = []
        brands = Brand.objects.all()
        for brand in brands:
            brand_list.append({
                'id': brand.id,
                'name': brand.name
            })
        search_list = {
            1: 'پربازدید ترین',
            2: 'پر طرفدار ترین',
            3: 'محبوب ترین',
            4: 'ارزان ترین',
            5: 'گران ترین',
            6: 'جدید ترین'
        }
        category_list = []
        parent_list = []
        sub_list = []
        subsub_list = []
        for category in Category.objects.filter(parent=None):
            parent_list.append({
                'id': category.id,
                'category': category.title
            })
        for sub in Category.objects.filter(parent__isnull=False, parent__parent=None):
            sub_list.append({
                'id': sub.id,
                'category': sub.title
            })
        for subsub in Category.objects.filter(parent__parent__isnull=False):
            subsub_list.append({
                'id': subsub.id,
                'category': subsub.title
            })
        for p in parent_list:
            category_list.append({
                'id': p['id'],
                'category': p['category'],
                'sub_category': []
            })
        for sub in sub_list:
            cat = Category.objects.get(title=sub['category'])
            index = 0
            for ind, i in enumerate(category_list):
                if i['category'] == cat.parent.title:
                    index = ind
            category_list[index]['sub_category'].append({
                'id': cat.id,
                'category': cat.title,
                'sub_sub_category': []
            })
        for subsub in subsub_list:
            cat = Category.objects.get(title=subsub['category'])
            index1 = 0
            index2 = 0
            for ind, i in enumerate(category_list):
                if i['category'] == cat.parent.parent.title:
                    index1 = ind
                    for ind2, j in enumerate(category_list[index1]['sub_category']):
                        if j['category'] == cat.parent.title:
                            index2 = ind2
            category_list[index1]['sub_category'][index2]['sub_sub_category'].append({
                'id': cat.id,
                'category': cat.title
            })

        res = {
            'sellers': seller_list,
            'brands': brand_list,
            'sortby': search_list,
            'category': category_list
        }
        return Response(res)


class Search(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        value = {}
        result = []
        new_result = []
        finall_result = []
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        brand = self.request.GET.get('brand')
        seller = self.request.GET.get('seller')
        minprice = self.request.GET.get('minprice')
        maxprice = self.request.GET.get('maxprice')
        sortby = self.request.GET.get('sortby')
        inventory = self.request.GET.get('inventory')

        if q:
            if '-' in q:
                q = q.split('-')
            elif ',' in q:
                q = q.split(',')
            elif '،' in q:
                q = q.split('،')
            else:
                q = [q, ]
            value['q'] = q
            for i in q:
                if len(i):
                    query = ProductFieldFeaturesValue.objects.filter(
                        Q(field__product__name__icontains=i) | Q(field__product__description__icontains=i) | Q(
                            field__product__summary__icontains=i)).filter(field__product__adminConfirm=True)[:25]
                    for qu in query:
                        if qu not in result:
                            result.append(qu)

                    query2 = ProductFieldFeaturesValue.objects.filter(field__product__category__title=i).filter(
                        field__product__adminConfirm=True)[:25]
                    for qu2 in query2:
                        if qu2 not in result:
                            result.append(qu2)

                    query3 = ProductFieldFeaturesValue.objects.filter(field__product__brand__name=i,
                                                                      field__product__adminConfirm=True)[:25]
                    for qu3 in query3:
                        if qu3 not in result:
                            result.append(qu3)
        else:
            query = ProductFieldFeaturesValue.objects.filter(field__product__adminConfirm=True)[:25]
            for qu in query:
                if qu not in result:
                    result.append(qu)
        if seller:
            value['seller'] = seller
            list = []
            for res in result:
                if res.field.seller.id == int(seller):
                    list.append(res)
            result = list

        if brand:
            value['brand'] = brand
            list = []
            brand = brand
            if brand:
                if '-' in brand:
                    brand = brand.split('-')
                elif ',' in brand:
                    brand = brand.split(',')
                elif '،' in brand:
                    brand = brand.split('،')
                else:
                    brand = [brand, ]
                for i in brand:
                    if len(i):
                        for res in result:
                            if res.field.product.brand.id == int(i):
                                list.append(res)
                    else:
                        list = result
                result = list

        if category:
            value['category'] = category
            try:
                cat = Category.objects.get(pk=category)
            except Category.DoesNotExist:
                return Response('مقدار category نامعتبر است')
            list = []
            for res in result:
                if cat.parent and not cat.parent.parent:
                    features = ProductFieldFeaturesValue.objects.filter(Q(pk=res.id) &
                                                                        (Q(field__product__category__id=int(
                                                                            category)) | Q(
                                                                            field__product__category__parent__id=int(
                                                                                category))))
                    for feature in features:
                        list.append(feature)
                elif cat.parent and cat.parent.parent:
                    features = ProductFieldFeaturesValue.objects.filter(Q(pk=res.id) &
                                                                        Q(field__product__category__id=int(category)))
                    for feature in features:
                        list.append(feature)
                else:
                    features = ProductFieldFeaturesValue.objects.filter(Q(pk=res.id) &
                                                                        (Q(field__product__category__id=int(
                                                                            category)) | Q(
                                                                            field__product__category__parent__id=int(
                                                                                category)) | Q(
                                                                            field__product__category__parent__parent__id=int(
                                                                                category))))
                    for feature in features:
                        list.append(feature)
            result = list

        if inventory:
            value['fillter'] = 'inventory'
            list = []
            for res in result:
                if inventory == 'true':
                    if res.inventory > 0:
                        list.append(res)
                elif inventory == 'false':
                    list.append(res)
                else:
                    return Response('پارامتر inventory باید مقدار true یا false باشد')
            result = list

        if minprice:
            value['fillter'] = 'minprice'
            list = []
            for res in result:
                if res.get_price_after_discount_and_taxation() > int(minprice):
                    list.append(res)
            result = list

        if maxprice:
            value['fillter'] = 'maxprice'
            list = []
            for res in result:
                if res.get_price_after_discount_and_taxation() < int(maxprice):
                    list.append(res)
            result = list
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
        createLog('Get', user, 'search/', ip, os_browser, value)
        # ----------------------------------------
        result.sort(key=lambda x: x.get_price_after_discount_and_taxation(), reverse=False)
        for res in result:
            finall_result.append({
                'product_id': res.field.product.id,
                'productfield_id': res.field.id,
                'productfeaature_id': res.id,
                'name': res.field.product.name,
                'exist': 'موجود' if res.inventory else 'ناموجود',
                'seller': res.field.seller.title,
                'brand': res.field.product.brand.name,
                'category': res.field.product.category.title,
                'image': res.field.product.get_absolute_url(),
                'price': res.get_price(),
                'price_with_taxation': res.get_price_after_taxation(),
                'discount_price': res.get_price_after_discount_and_taxation(),
                'discountPersent': res.field.discountPersent,
                'like_num': res.field.product.like_number,
                'sell_num': res.field.sell_number,
                'most_visit': res.field.product.visit,
            })
        for f in finall_result:
            status = False
            for index, new in enumerate(new_result):
                if f['product_id'] == new['product_id']:
                    status = True
            if not status:
                new_result.append({
                    'productfeature_id': f['productfeaature_id'],
                    'product_id': f['product_id'],
                    'productfield_id': f['productfield_id'],
                    'name': f['name'],
                    'exist': f['exist'],
                    'seller': f['seller'],
                    'brand': f['brand'],
                    'category': f['category'],
                    'image': f['image'],
                    'price': f['price'],
                    'price_with_taxation': f['price_with_taxation'],
                    'discount_price': f['discount_price'],
                    'discountPersent': f['discountPersent'],
                    'like_num': f['like_num'],
                    'sell_num': f['sell_num'],
                    'most_visit': f['most_visit'],
                })

        if sortby:
            if sortby == '1':
                value['sortby'] = 'most-visit'
                new_result = sorted(new_result, key=operator.itemgetter('like_num'), reverse=False)
            elif sortby == '2':
                value['sortby'] = 'sell'
                new_result = sorted(new_result, key=operator.itemgetter('sell_num'), reverse=False)
            elif sortby == '3':
                value['sortby'] = 'like'
                new_result = sorted(new_result, key=operator.itemgetter('most_visit'), reverse=False)
            elif sortby == '4':
                value['sortby'] = 'inexpensive'
                new_result = sorted(new_result, key=operator.itemgetter('discount_price'), reverse=False)
            elif sortby == '5':
                value['sortby'] = 'expensive'
                new_result = sorted(new_result, key=operator.itemgetter('discount_price'), reverse=True)
            elif sortby == '6':
                value['sortby'] = 'newest'
                new_result = sorted(new_result, key=operator.itemgetter('productfeature_id'), reverse=True)
            else:
                return Response('پارامتر sortby باید مقداری بین 1 تا 6 باشد')
        result_page = self.paginate_queryset(new_result, self.request, view=self)
        return self.get_paginated_response(result_page)


class SearchAA(APIView, StandardResultsSetPagination):

    def get(self, request, *args, **kwargs):
        value = {}
        result = []
        # seprate string for search

        if self.request.GET.get('search') == 'brand':
            value['search'] = 'brand'
            result = []
            for i in q:
                if len(i):
                    query3 = Product.objects.filter(brand__name=i, adminConfirm=True)[:25]
                    for qu3 in query3:
                        if qu3 not in result:
                            result.append(qu3)

        # Sort by related product by category
        if self.request.GET.get('sortby') == 'related':
            value['sortby'] = 'related'
            list = []
            list2 = []
            for res in result:
                p = ProductFieldFeaturesValue.objects.filter(field__product__category=res.category).order_by('price')
                if p:
                    list.append(p)
            list.sort(key=operator.attrgetter('price'), reverse=True)
            for li in list:
                list2.append(Product.objects.get(pk=li.product.id))
            result = list2

        # Fillter in result search by price
        if self.request.GET.get('fillter') == 'price':
            value['fillter'] = 'price'
            min = None
            max = None
            if self.request.GET.get('min'):
                min = float(self.request.GET.get('min'))
            if self.request.GET.get('max'):
                max = float(self.request.GET.get('max'))
            list = []
            for res in result:
                product_field = ProductFieldFeaturesValue.objects.filter(field__product=res.id).order_by('price')
                if product_field:
                    if min and max:
                        if product_field.get_price_after_discount_and_taxation() < max and product_field.get_price_after_discount_and_taxation() > min:
                            list.append(res)
                    if max and not min:
                        if product_field.get_price_after_discount_and_taxation() < max:
                            list.append(res)
                    if min and not max:
                        if product_field.get_price_after_discount_and_taxation() > min:
                            list.append(res)
            result = list

        # Fillter in result search by inventory

        # Filter on products sent by the seller
        if self.request.GET.get('fillter') == 'sentway':
            value['fillter'] = 'sentway'
            list = []
            for res in result:
                product_field = ProductFieldFeaturesValue.objects.filter(field__product=res.id).order_by('price')
                # if product field exist
                if product_field and product_field.field.seller.sendWay:
                    list.append(res)
            result = list

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
        createLog('Get', user, 'search/', ip, os_browser, value)
        # ----------------------------------------
        result_page = self.paginate_queryset(result, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        return self.get_paginated_response(serializer.data)


# Products with high comments
class MainMoreComment(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        more_comment_product = ProductField.objects.all().order_by('-comment_number')[:10]
        result_page = self.paginate_queryset(more_comment_product, self.request, view=self)
        more_comment_serializer = ProductSerializerForListDiscountPrice(result_page, many=True)
        serializer = ({"more_comment": more_comment_serializer.data})
        return self.get_paginated_response(serializer)


# Products with high likes
class MainMoreLike(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        more_like_product = Product.objects.all().order_by('-like_number')[:10]
        result_page = self.paginate_queryset(more_like_product, self.request, view=self)
        more_like_serializer = ProductSerializerForRelated(result_page, many=True)

        serializer = ({"more_like": more_like_serializer.data})
        return self.get_paginated_response(serializer)


# Random products with high like
class MainRandomMoreLike(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        randoms_like_product = []
        products_like_product = []
        list_random_like_product = []
        while len(randoms_like_product) < 10:
            query = random.randrange(0, len(Product.objects.all()))
            randoms_like_product.append(query)
        for rand in randoms_like_product:
            products_like_product.append(Product.objects.all().order_by('like_number')[rand])
        for product in products_like_product:
            if product not in list_random_like_product:
                list_random_like_product.append(product)
        result_page = self.paginate_queryset(list_random_like_product, self.request, view=self)
        randoms_like_serializer = ProductSerializerForRelated(result_page, many=True)

        serializer = ({"randoms_like": randoms_like_serializer.data})
        return self.get_paginated_response(serializer)


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


# Products with high visit
class MainMoreVisit(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        list_index = []
        more_visit_product = Product.objects.all().order_by('-visit')[:10]
        result = numpy.array_split(more_visit_product, 4)
        for res in result:
            list_index.append(res)
        # result_page = self.paginate_queryset(list_index[0]['result'], self.request, view=self)
        if len(list_index) >= 4:
            more_visit_serializer1 = ProductSerializerForRelated(list_index[0], many=True)
            more_visit_serializer2 = ProductSerializerForRelated(list_index[1], many=True)
            more_visit_serializer3 = ProductSerializerForRelated(list_index[2], many=True)
            more_visit_serializer4 = ProductSerializerForRelated(list_index[3], many=True)
            serializer = ({"more_visit1": more_visit_serializer1.data, "more_visit2": more_visit_serializer2.data,
                           "more_visit3": more_visit_serializer3.data, "more_visit4": more_visit_serializer4.data})
            return Response(serializer)
        more_visit_serializer1 = ProductSerializerForRelated(more_visit_product, many=True)
        serializer = ({"more_visit": more_visit_serializer1.data})
        return Response(serializer)


# Products with high comments
class MainSpecialOfferAndMediaBrandAndDiscountPriceAndRandomBrand(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        spicial_offers = ProductField.objects.filter(specialoffer=True)
        spicial_offer_serializer = ProductSerializerForList(spicial_offers, many=True)

        media_brands_banner_brand = []
        for brand in Brand.objects.filter(specialoffer=True)[:10]:
            media_brands_banner_brand.append(brand)
        result_page1 = self.paginate_queryset(media_brands_banner_brand, self.request, view=self)
        media_banner_brand_serializer = BrandSerializerForImageBanner(result_page1, many=True)

        list_discount_price = []
        discount_price_products = ProductField.objects.all()[:10]
        for discount_price_product in discount_price_products:
            if discount_price_product.discountPersent:
                list_discount_price.append(discount_price_product)
        result_page2 = self.paginate_queryset(list_discount_price, self.request, view=self)
        discount_price_serializer = ProductSerializerForListDiscountPrice(result_page2, many=True)

        randoms_random_brand = []
        brands_random_brand = []
        while len(randoms_random_brand) < 10:
            query = random.randrange(0, len(Brand.objects.all()))
            randoms_random_brand.append(query)
        for rand in randoms_random_brand:
            if Brand.objects.all()[rand] not in brands_random_brand:
                brands_random_brand.append(Brand.objects.all()[rand])
        result_page3 = self.paginate_queryset(brands_random_brand, self.request, view=self)
        random_brand_serializer = BrandSerializerForList(result_page3, many=True)

        serializer = (
            {"spicial_offers": spicial_offer_serializer.data},
            {"media_banner_brand_offer": media_banner_brand_serializer.data},
            {"discount_price_offer": discount_price_serializer.data}, {"random_brand": random_brand_serializer.data})
        return self.get_paginated_response(serializer)


# Main 3 momentory product
class MainMomentaryProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        randoms_random_product = []
        products_random_product = []
        list = []
        while len(randoms_random_product) < 3:
            query = random.randrange(0, len(Product.objects.all()))
            randoms_random_product.append(query)
        for rand in randoms_random_product:
            products_random_product.append(Product.objects.all()[rand])
        for product in products_random_product:
            if product not in list:
                list.append(product)
        result_page = self.paginate_queryset(products_random_product, self.request, view=self)
        random_product_serializer = ProductSerializerForRelated(result_page, many=True)
        serializer = ({"random_product": random_product_serializer.data})
        return self.get_paginated_response(serializer)


# popular category
class MainAdvocateCategory(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        advocate_category = []
        advocate_subcategory = []
        categories = Category.objects.filter(advocate=True, parent=None)
        for cat in categories:
            if cat not in advocate_category:
                advocate_category.append(cat)
        result_page1 = self.paginate_queryset(advocate_category, self.request, view=self)
        advocate_category_serializer = CategorySerializer(result_page1, many=True)

        categories2 = Category.objects.filter(advocate=True)
        for cat in categories2:
            if cat.parent is not None and cat not in advocate_subcategory:
                advocate_subcategory.append(cat)
        result_page2 = self.paginate_queryset(advocate_subcategory, self.request, view=self)
        advocate_sub_category_serializer = SubCategorySerializer(result_page2, many=True)

        serializer = (
            {"advocate_category": advocate_category_serializer.data},
            {"advocate_sub_category": advocate_sub_category_serializer.data})
        return self.get_paginated_response(serializer)


# Newest and bestsellers product
class MainLatestAndMoreSellProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        latest_products = ProductField.objects.all().order_by('-id')[:10]
        result_page1 = self.paginate_queryset(latest_products, self.request, view=self)
        latest_products_serializer = ProductSerializerForListDiscountPrice(result_page1, many=True)

        more_sell_product = ProductField.objects.all().order_by('-sell_number')[:10]
        result_page2 = self.paginate_queryset(more_sell_product, self.request, view=self)
        more_sell_serializer = ProductSerializer(result_page2, many=True)

        serializer = (
            {"latest_products": latest_products_serializer.data},
            {"more_sell": more_sell_serializer.data})
        return self.get_paginated_response(serializer)


# More visited products of user
class MainVisitedProductOfUser(ListAPIView):
    serializer_class = VisitedProductSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        try:
            user = User.objects.get(pk=self.request.user.id)
            userr = user.username
        # if user does not exist
        except User.DoesNotExist:
            userr = 'anonymous'
            # create log
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            os_browser = self.request.META['HTTP_USER_AGENT']
            createLog('Get', userr, f'main-visited-product-user/', ip, os_browser)
            # ----------------------------------------
            return []
        # create log
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        os_browser = self.request.META['HTTP_USER_AGENT']
        createLog('Get', userr, f'main-visited-product-user/', ip, os_browser)
        # ----------------------------------------
        visit = Visited.objects.filter(user=user).order_by('-id')[:10]
        return visit


# Related visited products of user
class MainRelatedVisitedProductOfUser(ListAPIView):
    serializer_class = ProductSerializerForRelated
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        list = []
        try:
            user = User.objects.get(pk=self.request.user.id)
        # if user does not exist
        except User.DoesNotExist:
            return []
        try:
            order = Order.objects.get(user=self.request.user, orderStatus='1')
        # if order does not exist
        except Order.DoesNotExist:
            return []
        for i in order.orderOrderitem.all():
            products = Product.objects.filter(
                Q(category=i.productfield.field.product.category) | Q(
                    category__parent=i.productfield.field.product.category))
            for p in products:
                if i.productfield.field.product != p:
                    list.append(p)
        return list


# Get random brands image and video
class RandomBrandBanner(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        randoms_random_brand = []
        banners_random_banner = []
        list = []
        v_randoms_random_brand = []
        v_banners_random_banner = []
        v_list = []
        while len(randoms_random_brand) < 10:
            query = random.randrange(0, len(ImageBanner.objects.all()))
            randoms_random_brand.append(query)
        for rand in randoms_random_brand:
            banners_random_banner.append(ImageBanner.objects.all()[rand])
        for banner in banners_random_banner:
            if banner not in list:
                list.append(banner)
        result_page = self.paginate_queryset(list, self.request, view=self)
        i_serializer = ImageBannerSerializerForGet(result_page, many=True)

        while len(v_randoms_random_brand) < 10:
            query = random.randrange(0, len(VideoBanner.objects.all()))
            v_randoms_random_brand.append(query)
        for rand in v_randoms_random_brand:
            v_banners_random_banner.append(VideoBanner.objects.all()[rand])
        for banner in v_banners_random_banner:
            if banner not in v_list:
                v_list.append(banner)
        result_page = self.paginate_queryset(v_list, self.request, view=self)
        v_serializer = VideoBannerSerializerForGet(result_page, many=True)
        return self.get_paginated_response({'images': i_serializer.data, 'video': v_serializer.data})
