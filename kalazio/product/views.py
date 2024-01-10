from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.views import APIView

from log.views import createLog
from questionAndAnswer.models import QuestionAndAnswer
from report.models import Report
from report.serializers import ReportSerializer, ReportSerializerForCreate
from user.models import User
from .models import (
    Product,
    FavoriteProduct,
    Seller,
    Category,
    Visited, ProductField, SpicialField, SpicialFieldValue, CategorySpicialField, ProductSpicialField, RateProduct,
    UserEvidence, Evidence, ProductFieldFeaturesValue,
    # ApplyingForProduct,
)
from .serializers import (
    ProductSerializer,
    SellerBrandSerializer,
    CategorySerializer,
    SubCategorySerializer,
    CategorySerializerForListProduct,
    ProductOfSellerSerializer,
    SellerSerializer,
    CategorySerializerForSearchInCategory,
    VisitedProductSerializer,
    ProductSerializerForList,
    ProductSerializerForListDiscountPrice,
    ProductSerializerForRelated,
    SpicialFieldSerializer,
    FavoriteProductSerializer,
    FavoriteProductSerializerForGetFavoriteList,
    # ApplyingForProductSerializer,
    WarrantySerializer, ProductSerializerForAllProduct, ProductSerializerForComparision,
    EvidenceSerializerCreate, EvidenceSerializerGet,
)
from comments.serializers import CommentSerializer, LikeCommentSerializer
from questionAndAnswer.serializers import QuestionAndAnswerSerializer, LikeQuestionAndAnswerSerializer
from questionAndAnswer import models
from comments.models import Comment, LikeComment as Like, Rate, GoodPoint, WeakPoint, DisLikeComment, ImageComment
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from Kalazio.pagination import StandardResultsSetPagination
from brand.models import Brand
from user.permissions import UserIsOwnerOrReadOnly
from brand.serializers import BrandSerializer, BrandSerializerForList, BrandSerializerForImageBanner
from Kalazio.pagination import StandardResultsSetPagination, FavoritrResultsSetPagination
from rest_framework.permissions import IsAuthenticated


# Create your views here.


# Get brands of seller :info
class BrandSeller(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = SellerBrandSerializer
    queryset = Seller.objects.all()


# Get all categories :info
class AllCategory(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = CategorySerializerForListProduct

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
        createLog('Get', userr, f'products/all-category/', ip, os_browser)
        # ----------------------------------------
        return Category.objects.all()


# Get root Categories :info
class AllMainCategory(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = CategorySerializerForListProduct

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
        createLog('Get', userr, f'products/all-main-category/', ip, os_browser)
        # ----------------------------------------
        return Category.objects.filter(parent=None)


# Get Subcategory of categories :info
class CategoryChild(APIView):
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
        createLog('Get', userr, f'products/all-category/{kwargs["pk"]}', ip, os_browser)
        # ----------------------------------------
        category = Category.objects.filter(parent=kwargs['pk'])
        serializer = CategorySerializerForListProduct(category, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get Products of category :info
@api_view(['GET'])
def product_of_category(request, id):
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
    createLog('Get', userr, f'products/category/{id}', ip, os_browser)
    # ----------------------------------------
    category = Category.objects.all()
    item = []
    item_product = []
    for cat in category:
        if cat.id == id and cat.parent:
            if cat.id == id and not cat.parent.parent:
                cat1 = Category.objects.get(id=id)
                cat2 = Category.objects.filter(parent=cat1)
                if cat2:
                    for c in cat2:
                        cat3 = Category.objects.filter(parent=c)
                        if cat3:
                            item.append(cat3)
                        else:
                            item.append(Category.objects.filter(title=c))
                item.append(Category.objects.filter(id=id))
                for it in item:
                    for i in it:
                        product = Product.objects.filter(category=i)
                        if product:
                            for p in product:
                                item_product.append(p)
                serializer = ProductSerializerForAllProduct(item_product, many=True)
                return Response(
                    {'parent_category': {'title': cat.parent.title, 'id': cat.parent.id}, 'result': serializer.data})
            elif cat.parent.parent:
                product = Product.objects.filter(category__id=id)
                if product:
                    for p in product:
                        item_product.append(p)
                serializer = ProductSerializerForAllProduct(item_product, many=True)
                return Response(
                    {'parent_category': {'title': cat.parent.title, 'id': cat.parent.id}, 'result': serializer.data})
            elif not cat.parent.parent:
                cat1 = Category.objects.get(id=id)
                products = Product.objects.filter(category=cat1)
                for product in products:
                    if product not in item_product:
                        item_product.append(product)
            serializer = ProductSerializerForAllProduct(item_product, many=True)
            return Response(serializer.data)
        elif cat.id == id:
            cat1 = Category.objects.get(id=id)
            cat2 = Category.objects.filter(parent=cat1)
            for c in cat2:
                cat3 = Category.objects.filter(parent=c)
                if cat3:
                    item.append(cat3)
                else:
                    item.append(Category.objects.filter(title=c))
            item.append(Category.objects.filter(id=id))
            item.append(Category.objects.filter(parent__id=id))
            for it in item:
                for i in it:
                    product = Product.objects.filter(category=i)
                    if product:
                        for p in product:
                            item_product.append(p)
            serializer = ProductSerializerForAllProduct(item_product, many=True)
            # return data : success
            return Response(serializer.data)
    return Response()


# Get sellers of a brand :info
class SellerOfBrand(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/seller-of-brand/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist :error
        except Brand.DoesNotExist:
            return Response('برند وجود ندارد')
        sellers = Seller.objects.filter(brand=brand)
        for seller in sellers:
            if seller.feature:
                list.append(seller)
        for seller in sellers:
            if seller not in list:
                list.append(seller)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = SellerBrandSerializer(result_page, many=True)
        # return data : success
        return self.get_paginated_response(serializer.data)


# -------------------------------------------------------------products api

# Get all products :info
class AllProduct(ListAPIView):
    pagination_class = StandardResultsSetPagination
    serializer_class = ProductSerializerForAllProduct

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
        createLog('Get', userr, f'products/all-products/', ip, os_browser)
        # ----------------------------------------
        return Product.objects.filter(productField__adminConfirm=True).order_by('-id')


# Get product details :info
class ProductDetail(APIView):
    pagination_class = None

    def get(self, *args, **kwargs):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/{pk}/', ip, os_browser)
        # ----------------------------------------
        try:
            product = Product.objects.get(pk=pk, adminConfirm=True)
        # if product does not exist :error
        except Product.DoesNotExist:
            return Response('محصول یافت نشد')
        try:
            field = ProductField.objects.filter(product=product, adminConfirm=True).first()
        # if product field does not exist :error
        except ProductField.DoesNotExist:
            return Response('محصول یافت نشد')
        documents = []
        for evi in product.evidence.all():
            # if user is authenticated :info
            if self.request.user.is_authenticated:
                u_evi = UserEvidence.objects.filter(evidence=evi, user=self.request.user)
                status = True
                if not u_evi:
                    status = False
                documents.append({'title': evi.title, 'apload': status,
                                  'status': u_evi.first().get_evidenceConfirm() if u_evi.first() else None})
            else:
                documents.append({'title': evi.title})
        rate = 0
        rate_count = 0
        question_count = 0
        liked = False
        # if user is authenticated :info
        if self.request.user.is_authenticated:
            try:
                rate = RateProduct.objects.get(user=self.request.user, product=product).rate
            # if rateProduct does not exist :error
            except RateProduct.DoesNotExist:
                rate = 0
            rate_count = RateProduct.objects.filter(user=self.request.user, product=product).count()
            question_count = QuestionAndAnswer.objects.filter(user=self.request.user, product=product).count()
            liked = FavoriteProduct.objects.filter(user=self.request.user, product=product).exists()
        # if user is authenticated :info
        if self.request.user.is_authenticated:
            try:
                visit = Visited.objects.get(product=product, user=self.request.user)
            # if visited does not exist :error
            except Visited.DoesNotExist:
                created = Visited.objects.create(product=product, user=self.request.user)
                product.visit += 1
                product.save()
        serializer = ProductSerializer(field)
        # return data :success
        return Response(
            {'rate': rate, 'rate_count': rate_count, 'question_count': question_count, 'liked': liked,
             'documents': documents, 'data': serializer.data})


# Get warranty of seller :info
class GetWarranty(ListAPIView):

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
        createLog('Get', userr, f'products/warranty-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده وجود ندارد')
        serializer = WarrantySerializer(seller.warranty)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)


# Comparision 2 product :info
class ComparisionProduct(ListAPIView):
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
        createLog('Get', userr, f'products/products-comparision/', ip, os_browser)
        # ----------------------------------------
        product1 = self.request.GET.get('product1')
        product2 = self.request.GET.get('product2')
        try:
            pro1 = Product.objects.get(pk=product1, adminConfirm=True)
            pro2 = Product.objects.get(pk=product2, adminConfirm=True)
        # if product does not exist :error
        except Product.DoesNotExist:
            return Response('محصول موجود نمی باشد')
        if pro1.category == pro2.category:
            serializer1 = ProductSerializerForComparision(pro1)
            serializer2 = ProductSerializerForComparision(pro2)
        # Products must be of the same category for comparison :warning
        else:
            return Response('محصولات برای مقایسه باید از یک دسته بندی باشند')
        # return data :success
        return Response({pro1.name: serializer1.data, pro2.name: serializer2.data}, status=status.HTTP_200_OK)


# Get products of seller :info
class ProductOfSeller(APIView, StandardResultsSetPagination):
    pagination_class = None

    def get(self, *args, **kwargs):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/products-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except:
            return Response('فروشگاه موجود نیست', status=status.HTTP_400_BAD_REQUEST)
        products = ProductField.objects.filter(seller=seller)
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForList(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Get sellers of a product :info
class SellerOfProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        list = []
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
        createLog('Get', userr, f'products/seller-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            product = Product.objects.get(pk=pk, adminConfirm=True)
        # if product does not exist :error
        except:
            return Response('محصول موجود نمی باشد')
        for seller in product.product_seller.all():
            if seller.feature and seller not in list:
                list.append(seller)
        for seller in product.product_seller.all():
            if seller not in list:
                list.append(seller)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = SellerSerializer(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Get comments of product :info
class CommentsOfProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        list = []
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
        createLog('Get', userr, f'products/comment-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            product = ProductField.objects.get(pk=pk, adminConfirm=True)
        # if productField does not exist :error
        except:
            return Response('محصول موجود نمی باشد')
        comments = Comment.objects.filter(product=product, confirm=True)
        for comment in comments:
            if comment not in list:
                list.append(comment)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = CommentSerializer(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Submit a report for comment :info
class ReportComment(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = ReportSerializerForCreate(data=request.data)
        if serializer.is_valid():
            objects = Report.objects.filter(comment=serializer.validated_data['comment'])
            for obj in objects:
                # This comment is in the list of your abuse reports :warning
                if obj.user == self.request.user:
                    return Response('این نظر در لیست گزارش تخلف شما موجود است')
            serializer.save()
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
            createLog('Post', userr, f'products/report-comment/', ip, os_browser, serializer.data)
            # ----------------------------------------
            # return data :success
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Like a comment :info
class LikeComment(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = LikeCommentSerializer(data=request.data)
        if serializer.is_valid():
            objects = Like.objects.filter(comment=serializer.validated_data['comment'])
            for obj in objects:
                # This comment is in the list of your abuse reports :warning
                if obj.user == self.request.user:
                    return Response('این نظر در لیست لایک های شما موجود است')
            serializer.save()
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
            createLog('Post', userr, f'products/like-comment/', ip, os_browser, serializer.data)
            # ----------------------------------------
            # return data :suucess
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# question and answers of product :info
class QuestionAndAnswerOfProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        list = []
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
        createLog('Get', userr, f'products/question-and-answer-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            product = Product.objects.get(pk=pk, adminConfirm=True)
        # if product does not exist :error
        except:
            return Response('محصول موجود نمی باشد')
        questionAndAnswers = QuestionAndAnswer.objects.filter(product=product, confirm=True)
        for questionAndAnswer in questionAndAnswers:
            if questionAndAnswer not in list and questionAndAnswer.parent == None:
                list.append(questionAndAnswer)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = QuestionAndAnswerSerializer(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Submit a report for question and answer :info
class ReportQuestionAndAnswer(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            objects = Report.objects.filter(user=self.request.user, questionAndAnswer=serializer.validated_data[
                'questionAndAnswer'])
            # This comment is in the list of your abuse reports : warning
            if objects:
                return Response('این نظر در لیست گزارش تخلف شما موجود است')
            serializer.save(user=self.request.user)
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
            createLog('Post', userr, f'products/report-question-answer/', ip, os_browser, serializer.data)
            # ----------------------------------------
            # return data : success
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Like question and answer :info
class LikeQuestionAndAnswer(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly)

    def post(self, request, *args, **kwargs):
        serializer = LikeQuestionAndAnswerSerializer(data=request.data)
        if serializer.is_valid():
            likes = models.LikeQuestionAndAnswer.objects.filter(user=self.request.user,
                                                                questionAndAnswer=serializer.validated_data[
                                                                    'questionAndAnswer'])
            # This comment is available in your likes list :warning
            if likes:
                return Response('این نظر در لیست لایک های شما موجود است')
            serializer.save(user=self.request.user)
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
            createLog('Post', userr, f'products/like-question-answer/', ip, os_browser, serializer.data)
            # ----------------------------------------
            # return data :success
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return error :error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get related product in detail product page by category :info
class RelatedProduct(APIView, StandardResultsSetPagination):
    def get(self, *args, **kwargs):
        list = []
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
        createLog('Get', userr, f'products/related-product/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            product = Product.objects.get(pk=pk, adminConfirm=True)
        # if product does not exist :error
        except:
            return Response('محصول موجود نمی باشد')
        if product.category.parent:
            parent_category = product.category.parent
            products = Product.objects.filter(category__parent=parent_category, adminConfirm=True)
        else:
            products = Product.objects.filter(category=product.category)
        if len(list) < 15:
            for pp in products:
                if pp not in list and pp.id != product.id:
                    list.append(pp)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializerForRelated(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Add product to favorite :info
@api_view(['POST'])
@permission_classes([IsAuthenticated, UserIsOwnerOrReadOnly])
def favorite_product_create(request, pk):
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
    createLog('Post', userr, f'products/favorite-product/{pk}', ip, os_browser, {'user': request.POST.get('user')})
    # ----------------------------------------
    try:
        query = FavoriteProduct.objects.get(user=request.user, product=pk)
    # if FavoriteProduct does not exist :error
    except FavoriteProduct.DoesNotExist:
        query = None
    if not query:
        try:
            product = Product.objects.get(id=pk, adminConfirm=True)
        except Product.DoesNotExist:
            return Response('محصول نامعتبر است', status=status.HTTP_400_BAD_REQUEST)
        product.like_number += 1
        product.save()
        FavoriteProduct.objects.create(user=request.user, product=product)
        return Response('ثبت شد', status=status.HTTP_201_CREATED)
    # Is duplicate :warning
    return Response('تکراری می باشد', status=status.HTTP_400_BAD_REQUEST)


# Get favorite products of user :info
class FavoriteProductsOfUser(APIView, FavoritrResultsSetPagination):
    permission_classes(IsAuthenticated, )
    pagination_class = FavoritrResultsSetPagination

    def get(self, request, *args, **kwargs):
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
        createLog('Get', userr, f'products/favorite-product-user/', ip, os_browser)
        # ----------------------------------------
        query = FavoriteProduct.objects.filter(user=request.user)
        result_page = self.paginate_queryset(query, request)
        serializer = FavoriteProductSerializerForGetFavoriteList(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Delete a product from favorite :info
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorite_product_delete(request, pk):
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
    createLog('Delete', userr, f'products/favorite-product-delete/{pk}', ip, os_browser)
    # ----------------------------------------
    try:
        query = FavoriteProduct.objects.get(user=request.user, product=pk)
    # if FavoriteProduct does not exist : error
    except FavoriteProduct.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if query:
        if request.method == 'DELETE':
            query.delete()
            product = Product.objects.get(id=pk, adminConfirm=True)
            product.like_number -= 1
            product.save()
            # return data :success
            return Response(status=status.HTTP_204_NO_CONTENT)
    # return error :error
    else:
        return Response('no product')


# ----------------------------------------------------------------seller api

# Get details of a seller :info
class DetailOfSeller(RetrieveAPIView):
    pagination_class = None
    serializer_class = SellerSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/detail-of-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        # return data :success
        return Seller.objects.filter(pk=pk)


# Get more visited products of seller :info
class MoreVisitProductOfSeller(APIView, StandardResultsSetPagination):
    pagination_class = StandardResultsSetPagination

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
        createLog('Get', userr, f'products/visited-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = Product.objects.filter(product_seller=seller, adminConfirm=True).order_by('-visit')
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# The seller's best-selling products :info
class MoreSellNumberProductOfSeller(APIView, StandardResultsSetPagination):
    pagination_class = StandardResultsSetPagination

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
        createLog('Get', userr, f'products/bestsellers-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد', status=status.HTTP_400_BAD_REQUEST)
        products = ProductField.objects.filter(seller=seller).order_by('price')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, adminConfirm=True)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Popular seller products :info
class MoreLikeProductOfSeller(APIView, StandardResultsSetPagination):
    pagination_class = StandardResultsSetPagination

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
        createLog('Get', userr, f'products/liked-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = Product.objects.filter(product_seller=seller, adminConfirm=True).order_by('-like_number')
        # if product not found :error
        if not len(products):
            return Response('محصول موجود نمی باشد', status=status.HTTP_400_BAD_REQUEST)
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Popular seller products :info
class MoreAdvocateProductOfSeller(APIView, StandardResultsSetPagination):

    def get(self, *args, **kwargs):
        list = []
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
        createLog('Get', userr, f'products/more-advocate-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = ProductField.objects.filter(seller=seller, adminConfirm=True).order_by('-advocate_number')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, adminConfirm=True)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Latest seller products :info
class LatestProductOfSeller(APIView, StandardResultsSetPagination):

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
        createLog('Get', userr, f'products/latest-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = Product.objects.filter(product_seller=seller, adminConfirm=True).order_by('-id')
        result_page = self.paginate_queryset(products, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Inexpensive seller products :info
class InExpensiveProductOfSeller(APIView, StandardResultsSetPagination):

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
        createLog('Get', userr, f'products/inexpensive-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = ProductField.objects.filter(seller=seller, adminConfirm=True).order_by('price')
        for product in products:
            obj = Product.objects.get(pk=product.product.id, adminConfirm=True)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Expensive seller products :info
class ExpensiveProductOfSeller(APIView, StandardResultsSetPagination):

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
        createLog('Get', userr, f'products/expensive-product-seller/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist :error
        except Seller.DoesNotExist:
            return Response('فروشنده موجود نمی باشد')
        products = ProductField.objects.filter(seller=seller, adminConfirm=True).order_by('-price')
        for product in products:
            obj = Product.objects.get(pk=product.product.id)
            if obj not in list:
                list.append(obj)
        result_page = self.paginate_queryset(list, self.request, view=self)
        serializer = ProductSerializerForAllProduct(result_page, many=True)
        # return data :success
        return self.get_paginated_response(serializer.data)


# Get all seller :info
class AllSeller(ListAPIView):
    serializer_class = SellerSerializer
    pagination_class = StandardResultsSetPagination

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
        createLog('Get', userr, f'products/all-seller/', ip, os_browser)
        # ----------------------------------------
        return Seller.objects.all()


# Commnets tab in product detail page :info
class CommentsTabOfProductDetail(APIView):

    def get(self, *args, **kwargs):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/comments-tab-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        ave_spicial = []
        # average rate :info
        ave_rate = 0
        comments_list = []

        product = Product.objects.get(pk=pk, adminConfirm=True)
        category = Category.objects.get(title=product.category)
        for sp in ProductSpicialField.objects.filter(product=product):
            if sp not in list:
                list.append(sp)
        for li in list:
            sum = 0
            if li:
                rates = Rate.objects.filter(spicialField=li.id)
                for rate in rates:
                    sum += int(rate.number)
                sum = sum / len(rates)
                ave_spicial.append({'key': li.value, 'rate': sum})
            else:
                return sum

        comments = Comment.objects.all()
        # sum comment point :info
        sum = 0
        for comment in comments:
            comments_list.append({'suggest': comment.suggest, 'title': comment.title, 'content': comment.content,
                                  'user': comment.user.first_name + ' ' + comment.user.last_name,
                                  'seller': comment.product.seller.title, 'date': str(comment.date),
                                  'status': comment.get_status(),
                                  'good_points': GoodPoint.objects.filter(comment=comment),
                                  'weak_points': WeakPoint.objects.filter(comment=comment),
                                  'like_count': Like.objects.all().count(),
                                  'dislike_count': DisLikeComment.objects.all().count()})
            sum += int(comment.point)
        ave_rate = sum / len(comments)
        # return data :success
        return Response({'special': ave_spicial, 'rate': ave_rate, 'comment_detail': comments_list},
                        status=status.HTTP_200_OK)


# Get special field in product detail page :info
class SpecialFieldTabOfProductDetail(APIView):

    def get(self, *args, **kwargs):
        pk = self.kwargs['pk']
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
        createLog('Get', userr, f'products/special-tab-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        product = Product.objects.get(pk=pk, adminConfirm=True)
        specials = ProductSpicialField.objects.filter(product=product)
        for special in specials:
            list.append({'key': special.spicialField.spicialField.key, 'value': special.spicialField.value})
        # return data :success
        return Response({'special': list}, status=status.HTTP_200_OK)


# Get each comment image in product detail page :info
class ProductImagesOfUsersOfProduct(APIView):
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
        createLog('Get', userr, f'products/images-comment-tab-of-product/{pk}', ip, os_browser)
        # ----------------------------------------
        list = []
        try:
            product = Product.objects.get(pk=pk)
        # if product does not exist :error
        except Product.DoesNotExist:
            return Response('محصول یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        images = ImageComment.objects.filter(comment__product__product=pk)
        for image in images:
            list.append(image.get_absolute_url())
            # return data :success
        return Response({'images': list}, status=status.HTTP_200_OK)


# Add the document required to purchase the product :info
class AddEvidence(APIView):
    permission_classes(IsAuthenticated, )

    def post(self, *args, **kwargs):
        try:
            evidence = Evidence.objects.get(title=self.request.GET.get('title'))
        # if Evidence does not exist :error
        except Evidence.DoesNotExist:
            return Response('مدرک یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        try:
            u_evi = UserEvidence.objects.get(evidence=evidence, user=self.request.user)
        # if UserEvidence does not exist :error
        except UserEvidence.DoesNotExist:
            serializer = EvidenceSerializerCreate(data=self.request.data)
            if serializer.is_valid():
                serializer.save(user=self.request.user, evidence=evidence)
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
                createLog('Post', userr, f'products/add-evidence/', ip, os_browser, serializer.data)
                # ----------------------------------------
                # return data :success
                return Response('ذخیره شد', status=status.HTTP_201_CREATED)
            # return error :error
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # The document has already been uploaded :warning
        return Response('مدرک قبلا اپلود شده است', status=status.HTTP_400_BAD_REQUEST)


# Get uploaded document :info
class GetEvidence(APIView):
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
        createLog('Get', userr, f'products/get-evidence/', ip, os_browser)
        # ----------------------------------------
        try:
            evidence = Evidence.objects.get(title=self.request.GET.get('title'))
        # if Evidence does not exist :error
        except Evidence.DoesNotExist:
            return Response('مدرک یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        try:
            u_evi = UserEvidence.objects.get(user=self.request.user, evidence=evidence)
        # if UserEvidence does not exist :error
        except UserEvidence.DoesNotExist:
            return Response('مدرک یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        serializer = EvidenceSerializerGet(u_evi)
        # return data :success
        return Response(serializer.data, status=status.HTTP_200_OK)
