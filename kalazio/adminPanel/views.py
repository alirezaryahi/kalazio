from django.shortcuts import render
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from brand.models import Brand, ImageBanner, VideoBanner
from order.models import OrderItem, Order, City, State
from order.serializers import OrderListSerializer
from product.models import (
    Seller,
    Warranty,
    SpicialField,
    Product,
    SpicialFieldValue,
    GalleryImage,
    GalleryVideo,
    ProductField,
    Category,
)
from product.serializers import (
    SellerBrandSerializerForEdit,
    ProductSerializerForCreate,
    ProductFieldSerializerForCreate,
    SpicialFieldSerializerForCreate,
    SpicialFieldValueSerializerForCreate,
    GalleryVideoSerializerForCreate,
    GalleryImageSerializerForCreate,
    SellerSerializerForList,
)
from user.models import User
from .models import BrandRepresentative, SellerRepresentative, Partner
from .serializers import (
    BrandRepresentativeSerializerForDetail,
    SellerRepresentativeForDetail,
    SellerRepresentativeForEdit,
    BrandRepresentativeSerializerForEdit,
    LoginSerializer,
    ProductSerializerForadminPanel,
    OrderSerializerForChangeOrderStatus,
    PartnerSerializer,
)
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    CreateAPIView,
    RetrieveAPIView,
)
from brand.serializers import (
    BrandSerializerForEdit,
    ImageBannerSerializerForEdit,
    VideoBannerSerializerForEdit,
    ImageBannerSerializerForGet,
    VideoBannerSerializerForGet,
    BrandOfSellerSerializer,
    CategorySerializerForListProduct,
)
from questionAndAnswer.serializers import (
    QuestionAndAnswerSerializerForCreate,
    QuestionAndAnswerSerializerForEdit,
    QuestionAndAnswerSerializerForDisable,
    QuestionAndAnswerSerializer,
)
from questionAndAnswer.models import QuestionAndAnswer
import datetime
from django.utils import timezone
import jdatetime


# Create your views here.

# Get orders of each seller
class OrderOfSeller(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        list = []
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        items = Order.objects.filter(orderOrderitem__seller=pk)
        for item in items:
            if item not in list:
                list.append(item)
        serializer = OrderListSerializer(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Change order status by seller
class OrderStatusChangeBySeller(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = Order.objects.get(pk=pk)
        # if order does not exist
        except Order.DoesNotExist:
            return Response("سفارش نا معتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = OrderSerializerForChangeOrderStatus(
            instance=order, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get Products Purchased of seller
class ProductsPurchasedOfSeller(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        list = []
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        items = OrderItem.objects.filter(
            order__orderStatus="1", productfield__seller=pk
        )
        for item in items:
            if item not in list:
                list.append(item.productfield)
        serializer = ProductSerializerForadminPanel(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get list of question and answers of seller
class ListQuestionAndAnswerOfSeller(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        query = QuestionAndAnswer.objects.filter(user=token.user)
        serializer = QuestionAndAnswerSerializer(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# disable answer
class DisableAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            question = QuestionAndAnswer.objects.get(pk=pk)
        # if question and answer does not exist
        except QuestionAndAnswer.DoesNotExist:
            return Response(
                "پرسش و پاسخ نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = QuestionAndAnswerSerializerForDisable(
            instance=question, data=request.data
        )
        if serializer.is_valid():
            serializer.save(confirm=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# enable question and answer
class EnableAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            question = QuestionAndAnswer.objects.get(pk=pk)
        # if question and answer does not exist
        except QuestionAndAnswer.DoesNotExist:
            return Response(
                "پرسش و پاسخ نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = QuestionAndAnswerSerializerForDisable(
            instance=question, data=request.data
        )
        if serializer.is_valid():
            serializer.save(confirm=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# edit question and answer
class EditQuestionAndAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            question = QuestionAndAnswer.objects.get(pk=pk)
        # if question and answer does not exist
        except QuestionAndAnswer.DoesNotExist:
            return Response(
                "پرسش و پاسخ نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        time = question.date + datetime.timedelta(days=2)
        now = jdatetime.date.today()
        # 2 days after registering the answer, you can edit it
        if now > time:
            return Response(
                "نهایت 2 روز پس از ثبت پاسخ میتوانید ان را ویرایش کنید",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if question.editNumber < 2:
            serializer = QuestionAndAnswerSerializerForEdit(
                instance=question, data=request.data
            )
            if serializer.is_valid():
                serializer.save()
                question.editNumber += 1
                question.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # No more than 2 edits are allowed
        return Response(
            "تعداد ویرایش بیشتر از 2 بار مجاز نیست", status=status.HTTP_400_BAD_REQUEST
        )


# Get brand list
class BrandList(ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandOfSellerSerializer


# Get category list
class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializerForListProduct


# Get seller list
class SellerList(ListAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializerForList


# Edit detail of each product
class ProductDetailEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            productfield = ProductField.objects.get(pk=pk, adminConfirm=True)
        # if product does not exist
        except Product.DoesNotExist:
            return Response("محصول نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductFieldSerializerForCreate(
            instance=productfield, data=request.data
        )
        if serializer.is_valid():
            serializer.save(
                product=productfield.product,
                inventory=int(serializer.validated_data["inventory"]),
                discountPersent=int(serializer.validated_data["discountPersent"]),
            )
            productfield.product.product_seller.add(
                Seller.objects.get(title=serializer.validated_data["seller"])
            )
            productfield.product.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# create product detail by seller
class ProductDetailCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = Product.objects.get(
                pk=request.POST.get("product"), adminConfirm=True
            )
        # if product does not exist
        except Product.DoesNotExist:
            return Response("محصول نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductFieldSerializerForCreate(data=request.data)
        if serializer.is_valid():
            serializer.save(
                product=product,
                inventory=int(serializer.validated_data["inventory"]),
                discountPersent=int(serializer.validated_data["discountPersent"]),
            )
            product.product_seller.add(
                Seller.objects.get(title=serializer.validated_data["seller"])
            )
            product.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# create full product by seller
class FullProductCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        product_serializer = ProductSerializerForCreate(data=self.request.data)
        if product_serializer.is_valid():
            product_serializer.save()
            product = Product.objects.get(
                name=product_serializer.validated_data["name"],
                description=product_serializer.validated_data["description"],
                summary=product_serializer.validated_data["summary"],
            )
            if request.POST.get("spicial_field_key"):
                kies = dict((request.data).lists())["spicial_field_key"]
                values = dict((request.data).lists())["spicial_field_value"]
                for index, key in enumerate(kies):
                    try:
                        sp_key = SpicialField.objects.get(key=key)
                    except SpicialField.DoesNotExist:
                        sp_key = SpicialField.objects.create(key=key)
                    sp_val = SpicialFieldValue.objects.create(
                        spicialField=sp_key, product=product, value=values[index]
                    )
                    product.spicialField.add(sp_key)
                    product.save()
            images = dict((request.data).lists())["images"]
            for image in images:
                if image:
                    # Photo size should not exceed 4 MB
                    if image.size > 4 * 1024 * 1024:
                        raise ValidationError("حجم عکس نباید بیشتر از 4 مگابایت باشد")
                    image_gallery = GalleryImage.objects.create(image=image)
                    product.imageGallery.add(image_gallery)
                    product.save()
            videos = dict((request.data).lists())["video"]
            for video in videos:
                if video:
                    # Movie size should not be more than 4 MB
                    if video.size > 10 * 1024 * 1024:
                        raise ValidationError("حجم فیلم نباید بیشتر از 4 مگابایت باشد")
                    video_gallery = GalleryVideo.objects.create(video=video)
                    product.videoGallery.add(video_gallery)
                    product.save()
            productfield_serializer = ProductFieldSerializerForCreate(data=request.data)
            if productfield_serializer.is_valid():
                productfield_serializer.save(
                    product=product,
                    inventory=int(productfield_serializer.validated_data["inventory"]),
                    discountPersent=int(
                        productfield_serializer.validated_data["discountPersent"]
                    ),
                )
                product.product_seller.add(
                    Seller.objects.get(
                        title=productfield_serializer.validated_data["seller"]
                    )
                )
                product.save()
                return Response(product_serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                productfield_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Edit brand
class BrandEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = self.request.GET.get("pk")
        try:
            brand = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=pk)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = BrandSerializerForEdit(instance=brand, data=self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Seller edit
class SellerEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = self.request.GET.get("pk")
        warranty = self.request.POST.get("warranty")
        warranty_name = self.request.POST.get("warranty_name")
        month = self.request.POST.get("month")
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            seller = Seller.objects.get(pk=pk)
        # if seller does not exist
        except Seller.DoesNotExist:
            return Response("فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = SellerBrandSerializerForEdit(
            instance=seller, data=self.request.data
        )
        if serializer.is_valid():
            if request.POST.get("city_limit"):
                cities = dict((request.data).lists())["city_limit"]
                for city in cities:
                    c = City.objects.get(city=city)
                    seller.city_limit.add(c)
            if request.POST.get("state_limit"):
                states = dict((request.data).lists())["state_limit"]
                for state in states:
                    s = State.objects.get(state=state)
                    seller.state_limit.add(s)
            if warranty_name:
                w = Warranty.objects.create(name=warranty_name, month=month)
                seller.warranty = w
                seller.save()
            else:
                w = Warranty.objects.get(pk=warranty)
                seller.warranty = w
                seller.save()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Clear the provincial restrictions for sending the seller
class StateLimitRemove(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        seller = Seller.objects.get(sellerRepresentative=token)
        try:
            state = State.objects.get(pk=pk)
        # if state does not exist
        except State.DoesNotExist:
            return Response(
                "استان مورد نظر یافت نشد", status=status.HTTP_400_BAD_REQUEST
            )
        seller.state_limit.remove(state)
        seller.save()
        # Successfully deleted
        return Response("با موفقیت پاک شد", status=status.HTTP_200_OK)


# Clear city restrictions for sending seller
class CityLimitRemove(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        seller = Seller.objects.get(sellerRepresentative=token)
        try:
            city = City.objects.get(pk=pk)
        # if city does not exist
        except City.DoesNotExist:
            return Response("شهر مورد نظر یافت نشد", status=status.HTTP_400_BAD_REQUEST)
        seller.city_limit.remove(city)
        seller.save()
        # Successfully deleted
        return Response("با موفقیت پاک شد", status=status.HTTP_200_OK)


# Get list of image banner
class ImageBannerList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        list = []
        for img in brand.imageBanner.all():
            list.append(img)
        serializer = ImageBannerSerializerForGet(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get image banner
class ImageBannerGet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        banner = self.request.GET.get("banner")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        try:
            banner = ImageBanner.objects.get(pk=banner)
        # if image banner does not exist
        except ImageBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = ImageBannerSerializerForGet(banner)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Delete image banner
class ImageBannerDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            banner = ImageBanner.objects.get(pk=pk)
        # if image banner does not exist
        except ImageBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        banner.delete()
        # Successfully deleted
        return Response("با موفقیت پاک شد", status=status.HTTP_200_OK)


# Update image banner
class ImageBannerUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            banner = ImageBanner.objects.get(pk=pk)
        # if image banner does not exist
        except ImageBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = ImageBannerSerializerForEdit(instance=banner, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create image banner
class ImageBannerCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response("توکن نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = ImageBannerSerializerForEdit(data=request.data)
        if serializer.is_valid():
            serializer.save()
            banner = ImageBanner.objects.filter(
                brand=serializer.validated_data["brand"]
            )
            brand.imageBanner.add(banner[0])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# List of video banner
class VideoBannerList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        list = []
        for video in brand.videoBanner.all():
            list.append(video)
        serializer = VideoBannerSerializerForGet(list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Get video banner
class VideoBannerGet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        banner = self.request.GET.get("banner")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        try:
            banner = VideoBanner.objects.get(pk=banner)
        # if video banner does not exist
        except VideoBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = VideoBannerSerializerForGet(banner)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Delete video banner
class VideoBannerDelete(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            banner = VideoBanner.objects.get(pk=pk)
        # if video banner does not exist
        except VideoBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        banner.delete()
        # Successfully deleted
        return Response("با موفقیت پاک شد", status=status.HTTP_200_OK)


# Update video banner
class VideoBannerUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            banner = VideoBanner.objects.get(pk=pk)
        # if video banner does not exist
        except VideoBanner.DoesNotExist:
            return Response("بنر نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = VideoBannerSerializerForEdit(instance=banner, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create video banner
class VideoBannerCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        brand = self.request.GET.get("brand")
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            brand = Brand.objects.get(pk=brand)
        # if brand does not exist
        except Brand.DoesNotExist:
            return Response("برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = VideoBannerSerializerForEdit(data=request.data)
        if serializer.is_valid():
            serializer.save()
            banner = VideoBanner.objects.filter(
                brand=serializer.validated_data["brand"]
            )
            brand.videoBanner.add(banner[0])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get detail of Brand Representative
class BrandRepresentativeDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = BrandRepresentativeSerializerForDetail(token)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Edit Brand Representative
class BrandRepresentativeEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        try:
            token = BrandRepresentative.objects.get(user=self.request.user)
        # if BrandRepresentative does not exist
        except BrandRepresentative.DoesNotExist:
            return Response(
                "نماینده برند نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = BrandRepresentativeSerializerForEdit(
            instance=token, data=self.request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get detail of Seller Representative
class SellerRepresentativeDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SellerRepresentativeForDetail(token)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Edit Seller Representative
class SellerRepresentativeEdit(UpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SellerRepresentativeForEdit(instance=token, data=self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login brand representative
@api_view(
    [
        "POST",
    ]
)
def brand_representative_login(request):
    check = False
    try:
        brand = User.objects.get(username=request.POST.get("username"), active=True)
        if brand.check_password(request.POST.get("password")):
            check = True
    # if user does not exist
    except User.DoesNotExist:
        return Response(
            "نام کاربری یا رمز عبور اشتباه است", status=status.HTTP_400_BAD_REQUEST
        )
    if check:
        try:
            token = Token.objects.get(user=brand)
        except Token.DoesNotExist:
            token = Token.objects.create(user=brand)
        return Response({"key": token.key}, status=status.HTTP_200_OK)
    else:
        # username or password was wrong
        return Response(
            "نام کاربری یا رمز عبور اشتباه است", status=status.HTTP_400_BAD_REQUEST
        )


# Brand representative logout
@api_view(
    [
        "DELETE",
    ]
)
def brand_representative_logout(request):
    token = Token.objects.get(user=request.user)
    token.delete()
    # Logout completed successfully
    return Response("خروج با موفقیت انجام شد", status=status.HTTP_200_OK)


# Seller representative login
@api_view(
    [
        "POST",
    ]
)
def seller_representative_login(request):
    check = False
    try:
        seller = User.objects.get(username=request.POST.get("username"), active=True)
        if seller.check_password(request.POST.get("password")):
            check = True
    # user does not exist
    except User.DoesNotExist:
        return Response(
            "نام کاربری یا رمز عبور اشتباه است", status=status.HTTP_400_BAD_REQUEST
        )
    if check:
        try:
            token = Token.objects.get(user=seller)
        except Token.DoesNotExist:
            token = Token.objects.create(user=seller)
        return Response({"key": token.key}, status=status.HTTP_200_OK)
    else:
        # Wrong username or password
        return Response(
            "نام کاربری یا رمز عبور اشتباه است", status=status.HTTP_400_BAD_REQUEST
        )


# Seller representative logout
@api_view(
    [
        "DELETE",
    ]
)
def seller_representative_logout(request):
    token = Token.objects.get(user=request.user)
    token.delete()
    # Logout completed successfully
    return Response("خروج با موفقیت انجام شد", status=status.HTTP_200_OK)


# Partner create
class PartnerCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, *args, **kwargs):
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PartnerSerializer(data=self.request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# List of partners
class PartnerList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        product = self.request.GET.get("product")
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            partners = Partner.objects.filter(productField=product)
        # if partner does not exist
        except Partner.DoesNotExist:
            return Response("سهیم نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = PartnerSerializer(partners, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Edit partner
class PartnerEdit(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        partner = self.request.GET.get("partner")
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        # if SellerRepresentative does not exist
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            partner = Partner.objects.get(pk=partner)
        # if partner does not exist
        except Partner.DoesNotExist:
            return Response("سهیم نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = PartnerSerializer(partner)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, *args, **kwargs):
        partner = self.request.GET.get("partner")
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            partner = Partner.objects.get(pk=partner)
        except Partner.DoesNotExist:
            return Response("سهیم نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        serializer = PartnerSerializer(data=self.request.data, instance=partner)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, *args, **kwargs):
        partner = self.request.GET.get("partner")
        try:
            token = SellerRepresentative.objects.get(user=self.request.user)
        except SellerRepresentative.DoesNotExist:
            return Response(
                "نماینده فروشنده نامعتبر است", status=status.HTTP_400_BAD_REQUEST
            )
        try:
            partner = Partner.objects.get(pk=partner)
        except Partner.DoesNotExist:
            return Response("سهیم نامعتبر است", status=status.HTTP_400_BAD_REQUEST)
        partner.delete()
        return Response("با موفقیت پاک شد", status=status.HTTP_200_OK)
