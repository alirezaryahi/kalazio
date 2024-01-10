import math

from django.db.models import Q
from jdatetime import datetime
from rest_framework import serializers
from product.serializers import ProductFieldSerializer, WarrantySerializer, SellerBrandSerializer
from .models import Order, State, City, Address, OrderItem, Finally, CancelOrder, NextOrderItem, Send
from product.models import Product, Category, SpicialFieldValue, ProductField, Warranty, Seller, \
    ProductFieldFeaturesValue, ProductSpicialField
from brand.serializers import BrandOfSellerSerializer
import jdatetime


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ('id', 'name', 'stateId')


class CitySerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = '__all__'

    def get_state(self, obj):
        return {
            'name': obj.state.name,
            'id': obj.state.id,
            'stateId': obj.state.stateId
        }


class FinallySerializerForList(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    send_price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    payWayOrder = serializers.SerializerMethodField()
    payWay = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()

    class Meta:
        model = Finally
        fields = ('user',
                  'order',
                  'order_id',
                  'products',
                  'address',
                  'date',
                  'time',
                  'ticket',
                  'SystemTraceNo',
                  'RetrivalRefNo',
                  'sendStatus',
                  'sendWayOrder',
                  'payWayOrder',
                  'changeStatus',
                  'payWay',
                  'pay',
                  'price',
                  'send_price',
                  'discount_price'
                  )

    def get_order_id(self, obj):
        return obj.order.order_id

    def get_payWay(self, obj):
        return obj.get_payWay()

    def get_payWayOrder(self, obj):
        return obj.get_payWayOrder()

    def get_time(self, obj):
        return str(jdatetime.datetime.fromgregorian(datetime=obj.time))

    def get_price(self, obj):
        return math.floor(obj.order.get_total_price())

    def get_send_price(self, obj):
        return math.floor(obj.order.sendPrice)

    def get_discount_price(self, obj):
        sum = 0
        for item in obj.order.orderOrderitem.all():
            sum += (item.productfield.get_price() * item.productfield.field.discountPersent) / 100
        return math.floor(sum)

    def get_products(self, obj):
        list = []
        for item in obj.order.orderOrderitem.all():
            list.append(item.productfield)
        serializer = ProductSerializerForOrderList(list, many=True)
        return serializer.data


class FinallySerializer(serializers.ModelSerializer):
    class Meta:
        model = Finally
        exclude = ('user', 'order', 'pay_date')


class CancelOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancelOrder
        exclude = ('user',)


class CategorySerializerForListProduct(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title')


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category = CategorySerializerForListProduct()
    brand = BrandOfSellerSerializer()

    class Meta:
        model = Product
        exclude = (
            'sell_number', 'like_number', 'comment_number', 'advocate_number', 'spicialField', 'share', 'visit',
            'inventory', 'product_seller')

    def get_image(self, obj):
        return obj.get_absolute_url()


class ProductSerializerForOrderList(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    warranty = serializers.SerializerMethodField()
    discountPersent = serializers.SerializerMethodField()
    discountPrice = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    feature = serializers.SerializerMethodField()

    class Meta:
        model = ProductFieldFeaturesValue
        fields = (
            'id', 'image', 'name', 'feature', 'get_price', 'total_price', 'warranty', 'discountPersent',
            'discountPrice', 'seller', 'brand')

    def get_feature(self, obj):
        return {
            'key': obj.key.title,
            'value': obj.value
        }

    def get_brand(self, obj):
        return obj.field.product.brand.name

    def get_seller(self, obj):
        return obj.field.seller.title

    def get_image(self, obj):
        return obj.field.product.get_absolute_url()

    def get_name(self, obj):
        return obj.field.product.name

    def get_total_price(self, obj):
        return obj.get_price_after_discount_and_taxation()

    def get_warranty(self, obj):
        try:
            object = Warranty.objects.get(name=obj.field.seller.warranty)
            serializer = WarrantySerializer(object)
            return serializer.data
        except Warranty.DoesNotExist:
            try:
                object = Warranty.objects.get(name=obj.field.warranty)
                serializer = WarrantySerializer(object)
                return serializer.data
            except:
                return None

    def get_discountPersent(self, obj):
        return obj.field.discountPersent

    def get_discountPrice(self, obj):
        price2 = (obj.get_price() * obj.field.discountPersent) / 100
        return math.ceil(price2)


class GetCompleteOrderSerializer(serializers.ModelSerializer):
    order_item = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    pay_date = serializers.SerializerMethodField()
    paymentNumber = serializers.SerializerMethodField()
    sendDate = serializers.SerializerMethodField()
    sendTime = serializers.SerializerMethodField()

    class Meta:
        model = Order
        exclude = ('rate',
                   'sendDate',
                   'sendTime',)

    def get_pay_date(self, obj):
        finall = Finally.objects.get(order=obj)
        return str(finall.pay_date)

    def get_paymentNumber(self, obj):
        finall = Finally.objects.get(order=obj)
        return finall.RetrivalRefNo

    def get_sendDate(self, obj):
        object = Send.objects.get(order=obj)
        return str(object.sendDate)

    def get_sendTime(self, obj):
        object = Send.objects.get(order=obj)
        return str(object.get_sendTime_display())

    def get_address(self, obj):
        i = []
        item = Finally.objects.get(order=obj)
        address = Address.objects.get(pk=item.address.pk)
        i.append({
            'state': address.state.name, 'city': address.city.name, 'postalCode': address.postalCode,
            'details': address.details,
            'nighbourhood': address.nighbourhood, 'plaque': address.plaque, 'floor': address.floor,
            'longitude': address.longitude, 'latitude': address.latitude
        })
        return i

    def get_total_price(self, obj):
        price = 0
        items = obj.finally_set.all()
        for item in items:
            price = item.get_price()
        return price

    def get_order_item(self, obj):
        i = []
        host = self.context['host']
        items = obj.orderitem_set.all()
        for item in items:
            list = []
            for spicialField in item.productfield.field.product.spicialField.all():
                spicial_value = SpicialFieldValue.objects.filter(spicialField=spicialField)
                for sp in spicial_value:
                    list.append({'key': spicialField.key,
                                 'products': {'id': sp.product.id, 'name': sp.product.name, 'value': sp.value}})
            i.append({'id': item.productfield.field.product.id, 'quantity': item.quantity,
                      'product': item.productfield.field.product.name,
                      'image': f'{host}{item.productfield.field.product.image.url}',
                      'price-unit': item.productfield.get_price_after_discount_and_taxation(),
                      'price-all': item.quantity * item.productfield.get_price_after_discount_and_taxation(),
                      'spicial_field': list,
                      'category': item.productfield.field.product.category.title, 'seller': item.seller.title,
                      'brand': item.productfield.field.product.brand.name,
                      'warranty': item.warranty.name})
        return i


class OrderItemListSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    warranty = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    price_discount = serializers.SerializerMethodField()
    price_without_discount = serializers.SerializerMethodField()
    amount_discount = serializers.SerializerMethodField()
    send_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    gift = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('order', 'product', 'warranty', 'seller', 'quantity', 'price_without_discount', 'price_discount',
                  'amount_discount', 'send_price', 'total_price', 'gift')

    def get_total_price(self, obj):
        return math.ceil(obj.order.get_total_price() + obj.order.sendPrice)

    def get_send_price(self, obj):
        return math.ceil(obj.order.sendPrice)

    def get_price_without_discount(self, obj):
        sum = 0
        if obj.order.gift:
            sum += obj.order.get_total_price_without_discount() - obj.order.gift.amount
        else:
            sum += obj.order.get_total_price_without_discount()
        return sum

    def get_gift(self, obj):
        if obj.order.gift:
            return {'giftId': obj.order.gift.id}
        else:
            return None

    def get_price_discount(self, obj):
        if obj.order.gift:
            return obj.order.get_total_price() - obj.order.gift.amount
        return obj.order.get_total_price()

    def get_amount_discount(self, obj):
        sum = 0
        sum = self.get_price_without_discount(obj) - self.get_price_discount(obj)
        return sum

    def get_product(self, obj):
        field = ProductField.objects.filter(id=obj.productfield.field.id)
        serializer = ProductFieldSerializer(field, many=True)
        return serializer.data

    def get_warranty(self, obj):
        objects = Warranty.objects.filter(name=obj.warranty)
        serializer = WarrantySerializer(objects, many=True)
        return serializer.data

    def get_seller(self, obj):
        objects = Seller.objects.filter(title=obj.productfield.field.seller)
        serializer = SellerBrandSerializer(objects, many=True)
        return serializer.data


class OrderItemListSerializerForOrderList(serializers.ModelSerializer):
    productfield = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'productfield', 'quantity')

    def get_productfield(self, obj):
        serializer = ProductSerializerForOrderList(obj.productfield)
        return serializer.data


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ('user',)


class OrderListSerializer(serializers.ModelSerializer):
    orderStatus = serializers.SerializerMethodField()
    orderItems = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    sendPrice = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    price_without_discount = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    quantity_all = serializers.SerializerMethodField()
    send_way_order = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'

    def get_send_way_order(self, obj):
        res = ''
        for i in obj.orderOrderitem.all():
            if i.productfield.field.seller.sendWay:
                res = 'ارسال توسط فروشنده'
                return res
        try:
            finall = Finally.objects.get(order=obj)
            res = finall.get_sendWayOrder()
            return res
        except Finally.DoesNotExist:
            return res

    def get_user(self, obj):
        try:
            return {
                'name': obj.user.first_name + ' ' + obj.user.last_name,
                'phone': obj.user.phone
            }
        except:
            return {
                'name': '',
                'phone': obj.user.phone
            }

    def get_quantity_all(self, obj):
        sum = 0
        for i in obj.orderOrderitem.all():
            sum += i.quantity
        return sum

    def get_orderStatus(self, obj):
        return obj.get_orderStatus()

    def get_orderItems(self, obj):
        list = []
        for item in obj.orderOrderitem.all():
            list.append(item)
        serializer = OrderItemListSerializerForOrderList(list, many=True)
        return serializer.data

    def get_total_price(self, obj):
        return math.ceil(obj.get_total_price() + obj.sendPrice)

    def get_sendPrice(self, obj):
        return math.ceil(obj.sendPrice)

    def get_price_without_discount(self, obj):
        sum = 0
        if obj.gift:
            sum += obj.get_total_price_without_discount() - obj.gift.amount
        else:
            sum += obj.get_total_price_without_discount()
        return sum

    def get_discount_price(self, obj):
        discount = 0
        without = 0
        for item in obj.orderOrderitem.all():
            if item.productfield.field.discountPersent:
                without += item.productfield.get_price() * item.quantity
                discount += item.productfield.get_price() - (((
                                                                      item.productfield.get_price() * item.productfield.field.discountPersent) / 100) * item.quantity)
        return without - discount


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class NextOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextOrderItem
        fields = ('productfield',)


class NextOrderItemListSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = NextOrderItem
        fields = '__all__'


class StateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'


class CityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class AddressSerializerRet(serializers.ModelSerializer):
    state = StateDetailSerializer(required=False)
    city = CityDetailSerializer(required=False)
    plaque = serializers.IntegerField(required=True)
    floor = serializers.IntegerField(required=False)
    details = serializers.CharField(style={'base_template': 'textarea.html'}, required=False)
    postalCode = serializers.CharField(required=False)

    class Meta:
        model = Address
        exclude = ('user',)


class AddressSerializerRetForEdit(serializers.ModelSerializer):
    plaque = serializers.IntegerField(required=True)
    floor = serializers.IntegerField(required=False)
    details = serializers.CharField(style={'base_template': 'textarea.html'}, required=False)
    postalCode = serializers.CharField(required=False)

    class Meta:
        model = Address
        exclude = ('user', 'city', 'state')


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ('user', 'state', 'city')


class OrderSerializerForOrders(serializers.ModelSerializer):
    order_date = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    send_price = serializers.SerializerMethodField()
    order_item = serializers.SerializerMethodField()
    order_status = serializers.SerializerMethodField()
    payWayOrder = serializers.SerializerMethodField()
    order_detail = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    serial = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    RetrivalRefNo = serializers.SerializerMethodField()
    payment_history = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'serial', 'RetrivalRefNo', 'order_date', 'price', 'discount_price', 'send_price', 'total_price',
            'payment_history', 'order_item', 'order_status', 'payWayOrder', 'order_detail', 'address')

    def get_serial(self, obj):
        return obj.order_id

    def get_payment_history(self, obj):
        payment_list = []
        finalls = Finally.objects.filter(Q(order=obj) and (Q(order__orderStatus='4') | Q(order__orderStatus='6')))
        if finalls:
            for finall in finalls:
                payment_list.append({
                    'RetrivalRefNo': finall.RetrivalRefNo,
                    'SystemTraceNo': finall.SystemTraceNo,
                    'date': finall.date,
                    'amount': finall.order.get_total_price_with_discount() + finall.order.sendPrice,
                    'status': True if finall.pay == '1' else False
                })
        return payment_list

    def get_RetrivalRefNo(self, obj):
        try:
            finall = Finally.objects.get(order=obj)
        except Finally.DoesNotExist:
            return None
        return finall.RetrivalRefNo if finall.RetrivalRefNo else 0

    def get_discount_price(self, obj):
        sum = 0
        for item in obj.orderOrderitem.all():
            sum += math.floor((item.productfield.get_price() * item.productfield.field.discountPersent) / 100)
        return sum

    def get_address(self, obj):
        try:
            fin = Finally.objects.get(order=obj)
        except:
            return ''
        serializer = AddressSerializerRet(fin.address)
        return serializer.data

    def get_order_detail(self, obj):
        list = []
        order = Order.objects.get(pk=obj.pk)
        if order.orderStatus == '4' or order.orderStatus == '6' or order.orderStatus == '8':
            try:
                finall = Finally.objects.get(order=order)
            except Finally.DoesNotExist:
                return ''
            list.append({
                'pay_date': str(finall.pay_date),
                'ticket': finall.ticket,
                'SystemTraceNo': finall.SystemTraceNo,
                'RetrivalRefNo': finall.RetrivalRefNo,
                'address': {
                    'state': finall.address.state.name,
                    'city': finall.address.city.name,
                    'postalCode': finall.address.postalCode,
                    'details': finall.address.details,
                    'nighbourhood': finall.address.nighbourhood,
                    'plaque': finall.address.plaque,
                    'floor': finall.address.floor
                }
            })
        else:
            list = []
        return list

    def get_payWayOrder(self, obj):
        try:
            finall = Finally.objects.get(order=obj)
        except Finally.DoesNotExist:
            return ''
        if finall.get_payWayOrder():
            return finall.get_payWayOrder()
        return ''

    def get_order_status(self, obj):
        return obj.get_orderStatus()

    def get_order_date(self, obj):
        try:
            finall = Finally.objects.get(order=obj)
        except Finally.DoesNotExist:
            return None
        return str(finall.date) if finall.date else 0

    def get_price(self, obj):
        sum = 0
        order_items = OrderItem.objects.filter(order=obj)
        if len(order_items) > 0:
            for item in order_items:
                sum += item.productfield.get_price_after_discount_and_taxation() * item.quantity
        return sum

    def get_send_price(self, obj):
        if obj.sendPrice:
            return round(obj.sendPrice)
        return 0

    def get_total_price(self, obj):
        return self.get_price(obj) + self.get_send_price(obj)

    def get_order_item(self, obj):
        list = []
        special_field = []
        warranty = None
        discount_price = 0
        order_items = OrderItem.objects.filter(order=obj)
        if len(order_items) > 0:
            for item in order_items:
                specials = ProductSpicialField.objects.filter(product=item.productfield.field.product)
                for special in specials:
                    special_field.append({
                        'key': special.spicialField.spicialField.key,
                        'value': special.spicialField.value
                    })
                if item.productfield.field.warranty:
                    warranty = item.productfield.field.warranty.name
                elif item.seller.warranty:
                    warranty = item.seller.warranty.name
                else:
                    warranty = None
                if item not in list:
                    if item.productfield.field.discountPersent > 0:
                        discount_price = (item.productfield.price * item.productfield.field.discountPersent) / 100
                    list.append({
                        'image': item.productfield.field.product.get_absolute_url(),
                        'brand': str(item.productfield.field.product.brand),
                        'seller': str(item.seller),
                        'special_field': special_field,
                        'warranty': str(warranty),
                        'name': item.productfield.field.product.name,
                        'quantity': item.quantity,
                        'price': item.productfield.get_price(),
                        'discount_price': discount_price if discount_price else 0,
                    })
        else:
            list = ['سبد خرید خالی است']
        return list
