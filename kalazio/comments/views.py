import json
from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from log.views import createLog
from order.models import Order
from product.models import Product, Category, SpicialFieldValue, ProductField, SpicialField
from product.serializers import SpicialFieldSerializerForCreate, SpicialFieldSerializer, \
    ProductSerializerForCommentsList
from user.models import User
from .models import Comment, LikeComment, Rate, ImageComment, VideoComment, WeakPoint, GoodPoint, DisLikeComment
from .serializers import CommentSerializerForCreate, LikeCommentSerializer, DisLikeCommentSerializer, CommentSerializer, \
    CommentSerializerForList
from user.permissions import UserIsOwnerOrReadOnly
from product.models import SpicialField


# Create your views here.

# Create like comment
class LikeCommentCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, *args, **kwargs):
        try:
            comment = Comment.objects.get(pk=self.request.POST.get('comment'))
        # if comment does not exist
        except Comment.DoesNotExist:
            return Response('کامنت یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        serializer = LikeCommentSerializer(data=self.request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
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
            createLog('Post', user, 'comment/like-comment/', ip, os_browser, serializer.data)
            # ----------------------------------------
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create dislike comment
class DisLikeCommentCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, *args, **kwargs):
        try:
            comment = Comment.objects.get(pk=self.request.POST.get('comment'))
        # if comment does not exist
        except Comment.DoesNotExist:
            return Response('کامنت یافت نشد', status=status.HTTP_400_BAD_REQUEST)
        serializer = DisLikeCommentSerializer(data=self.request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
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
            createLog('Post', user, 'comment/dislike-comment/', ip, os_browser, serializer.data)
            # ----------------------------------------
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create comment
class CreateComment(CreateAPIView):
    permission_classes = (IsAuthenticated, UserIsOwnerOrReadOnly,)

    def post(self, request, *args, **kwargs):
        serializer = CommentSerializerForCreate(data=request.data)
        if serializer.is_valid():
            product_field_id = serializer.validated_data['product_field_id']

            # Create detail rate with special field foreign key and rate
            if self.request.POST.get('spicialField') and self.request.POST.get('detailRate'):
                spicial = SpicialField.objects.get(pk=int(self.request.POST.get('spicialField')))
                detailRate = Rate.objects.create(spicialField=spicial, number=self.request.POST.get('detailRate'),
                                                 user=self.request.user)

            # Create image comment with list of image
            images = dict((request.data).lists())['image']
            if len(images) and len(images) < 5:
                for image in images:
                    if image:
                        # Photo size should not exceed 8 MB
                        if image.size > 8 * 1024 * 1024:
                            raise ValidationError("حجم عکس نباید بیشتر از 8 مگابایت باشد")
            # The number of submitted photos should not be more than 5
            if len(images) > 5:
                raise ValidationError("تعداد عکس ارسالی نباید بیشتر از 5 عدد باشد")

            # Create video comment with list of video
            videos = dict((request.data).lists())['video']
            if len(videos) and len(videos) < 3:
                for video in videos:
                    if video:
                        # Movie size should not exceed 100 MB
                        if video.size > 100 * 1024 * 1024:
                            raise ValidationError("حجم فیلم نباید بیشتر از 100 مگابایت باشد")
            # The number of submitted videos should not be more than 3
            if len(videos) > 3:
                raise ValidationError("تعداد فیلم ارسالی نباید بیشتر از 3 عدد باشد")

            # Create weak point with list of weak point
            weak_points = dict((request.data).lists())['weak_point']
            # The maximum number of weaknesses is 5
            if len(weak_points) > 5:
                raise ValidationError("حداکثر تعداد نقاط ضعف 5 عدد می باشد")

            # Create good point with list of good point
            good_points = dict((request.data).lists())['good_point']
            # The maximum number of strengths is 5
            if len(good_points) > 5:
                raise ValidationError("حداکثر تعداد نقاط قوت 5 عدد می باشد")

            # You have already posted a review for this product
            if Comment.objects.filter(product_field_id=product_field_id, user=self.request.user).exists():
                raise ValidationError("شما قبلا برای این محصول نظر ثبت کرده اید")
            c = serializer.save(user=self.request.user)
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
            createLog('Post', user, 'comment/create/', ip, os_browser, serializer.data)
            # ----------------------------------------
            comment = Comment.objects.filter(user=self.request.user).last()
            if len(images) and len(images) < 5:
                for image in images:
                    print(image)
                    if image:
                        print('byee')
                        ImageComment.objects.create(comment=comment, image=image)

            if len(videos) and len(videos) < 3:
                for video in videos:
                    if video:
                        VideoComment.objects.create(comment=comment, video=video)

            for weak_point in weak_points:
                weak_point = weak_point.replace(" ", "")
                if weak_point != '':
                    WeakPoint.objects.create(comment=comment, weak_text=str(weak_point))

            for good_point in good_points:
                good_point = good_point.replace(" ", "")
                if good_point != '':
                    GoodPoint.objects.create(comment=comment, good_text=good_point)

            if self.request.POST.get('spicialField') and self.request.POST.get('detailRate'):
                c.detailRate.add(detailRate)
            products = ProductField.objects.filter(adminConfirm=True)
            for product in products:
                if self.request.user in product.buy_users.all():
                    c.status = 'buyer'
            c.status = 'user'
            c.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImageComments(APIView):
    def get(self, *args, **kwargs):
        objects = {}
        images = ImageComment.objects.filter(comment__product_field_id=self.request.GET.get('product_field_id'))
        for image in images:
            objects['url'] = image.get_absolute_url()
        return Response(objects, status=status.HTTP_200_OK)


# Get comment list of user
class MyComments(APIView):
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
        createLog('Get', user, 'comment/my-comment/', ip, os_browser)
        # ----------------------------------------
        objects = Comment.objects.filter(user=self.request.user)
        serializer = CommentSerializer(objects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get list of comments awaiting approval
class WaitingComment(APIView):
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
        createLog('Get', user, 'comment/waiting-comment/', ip, os_browser)
        # ----------------------------------------
        comments = Comment.objects.filter(user=self.request.user, confirm=False)
        serializer = CommentSerializerForList(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
