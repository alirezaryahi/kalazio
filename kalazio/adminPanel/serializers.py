from rest_framework import serializers

from order.models import OrderItem, Finally, Order
from product.models import Product, ProductField
from .models import BrandRepresentative, SellerRepresentative, Partner


class BrandRepresentativeSerializerForDetail(serializers.ModelSerializer):
    class Meta:
        model = BrandRepresentative
        fields = "__all__"


class SellerRepresentativeForDetail(serializers.ModelSerializer):
    class Meta:
        model = SellerRepresentative
        fields = "__all__"


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = "__all__"


class BrandRepresentativeSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = BrandRepresentative
        exclude = ("active",)


class SellerRepresentativeForEdit(serializers.ModelSerializer):
    class Meta:
        model = SellerRepresentative
        exclude = ("active",)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})


class ProductSerializerForadminPanel(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    sendWay = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        fields = (
            "id",
            "name",
            "price",
            "discount_price",
            "image",
            "discountPersent",
            "sendWay",
            "user",
        )

    def get_discount_price(self, obj):
        return obj.get_price_after_commission()

    def get_name(self, obj):
        return obj.product.name

    def get_image(self, obj):
        return obj.product.get_absolute_url()

    def get_sendWay(self, obj):
        return obj.seller.sendWay

    def get_user(self, obj):
        list = []
        items = Finally.objects.filter(
            pay=True,
            order__orderOrderitem__productfield=obj.id,
            order__orderOrderitem__seller__sendWay=True,
        )
        for item in items:
            list.append(
                {
                    "firstname": item.user.first_name
                    if item.address.forMe
                    else item.address.firstname,
                    "lastname": item.user.last_name
                    if item.address.forMe
                    else item.address.lastname,
                    "phone": item.address.user.username
                    if item.address.forMe
                    else item.address.phone,
                    "state": item.address.state.name,
                    "city": item.address.city.name,
                    "postalCode": item.address.postalCode,
                    "plaque": item.address.plaque,
                    "details": item.address.details,
                }
            )
        return list


class OrderSerializerForChangeOrderStatus(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("orderStatus",)
