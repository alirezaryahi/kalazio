from django.db.models import Q
from rest_framework import serializers
from rest_framework.response import Response
from .models import Product, Seller, Category, SpicialField, FavoriteProduct, Visited, Warranty, ProductField, \
    GalleryVideo, GalleryImage, SpicialFieldValue, CategorySpicialField, ProductSpicialField, UserEvidence, \
    ProductFieldFeaturesValue
from brand.serializers import BrandOfSellerSerializer
from django.template.defaultfilters import truncatechars


class ProductSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'name',
            'brand',
            'image',
            'description',
            'summary',
            'category',
        )


class EvidenceSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = UserEvidence
        exclude = (
            'evidenceConfirm',
            'user',
            'evidence'
        )


class EvidenceSerializerGet(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = UserEvidence
        exclude = (
            'evidenceConfirm',
        )

    def get_file(self, obj):
        return obj.get_absolute_file()


class ProductFieldSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = ProductField
        fields = (
            'price',
            'discountPersent',
            'inventory',
            'taxation',
            'confirm',
            'specialoffer',
            'seller'
        )


class SpicialFieldSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = SpicialField
        fields = ('key',)


class SpicialFieldValueSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = SpicialFieldValue
        fields = ('value',)


class GalleryVideoSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = GalleryVideo
        fields = ('video',)


class GalleryImageSerializerForCreate(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ('image',)


class WarrantySerializer(serializers.ModelSerializer):
    class Meta:
        model = Warranty
        fields = '__all__'


class ProductFieldSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        exclude = ('confirm', 'specialoffer', 'sell_number', 'comment_number', 'advocate_number', 'seller', 'taxation')

    def get_product(self, obj):
        return obj.product.name

    def get_total_price(self, obj):
        return obj.get_price_after_discount_and_taxation()

    def get_price(self, obj):
        return obj.get_price()


# class ApplyingForProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ApplyingForProduct
#         fields = '__all__'


class SpicialFieldSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = SpicialField
        fields = '__all__'

    def get_value(self, obj):
        return SpicialFieldValue.objects.get(spicialField=obj).value


class ProductSerializerForListDiscountPrice(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    productfield_id = serializers.SerializerMethodField()
    get_price_after_discount_and_taxation = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        fields = (
            'id', 'productfield_id', 'get_name', 'image', 'get_price_after_discount_and_taxation',
            'discountPersent', 'get_rate', 'comment_number')

    def get_get_price_after_discount_and_taxation(self, obj):
        objects = []
        field = ProductFieldFeaturesValue.objects.filter(field=obj).order_by('-price').first()
        if field:
            return field.get_price_after_discount_and_taxation()
        return None

    def get_productfield_id(self, obj):
        return obj.id

    def get_id(self, obj):
        return obj.product.id

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_id(self, obj):
        return obj.product.id


class ProductSerializerForList(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        fields = ('id', 'name', 'image', 'price', 'discount_price', 'get_rate', 'comment_number')

    def get_name(self, obj):
        return obj.product.name

    def get_id(self, obj):
        return obj.product.id

    def get_image(self, obj):
        return obj.product.get_absolute_url()

    def get_discount_price(self, obj):
        objects = []
        field = ProductFieldFeaturesValue.objects.filter(field=obj).order_by('-price')
        if field:
            for f in field:
                objects.append({
                    'key': f.key.title,
                    'value': f.value,
                    'price': f.get_price_after_discount_and_taxation()
                })
        return objects

    def get_price(self, obj):
        objects = []
        field = ProductFieldFeaturesValue.objects.filter(field=obj).order_by('-price')
        if field:
            for f in field:
                objects.append({
                    'key': f.key.title,
                    'value': f.value,
                    'price': f.get_price()
                })
        return objects

    def get_comment_number(self, obj):
        return obj.comment_number


class FavoriteProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteProduct
        fields = '__all__'


class CategorySerializerForListProduct(serializers.ModelSerializer):
    spicialField = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'parent', 'title', 'spicialField')

    def get_parent(self, obj):
        return {'title': obj.parent.title, 'id': obj.parent.id} if obj.parent else None

    def get_spicialField(self, obj):
        list = []
        for spicialField in CategorySpicialField.objects.filter(category=obj):
            list.append({'key': spicialField.spicialField.spicialField.key, 'value': spicialField.spicialField.value})
        return list


class SellerBrandSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ('warranty_status',
                  'restore_status',
                  'restore',
                  'sendWay',
                  'payBySeller',
                  'phone',
                  'state',
                  'city',
                  'address')


class SellerBrandSerializer(serializers.ModelSerializer):
    brand = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = (
            'id', 'title', 'logo', 'brand', 'feature', 'date_joined', 'sendWay', 'state', 'city', 'address',
            'get_payment_method')

    def get_logo(self, obj):
        return obj.get_absolute_url()

    def get_brand(self, obj):
        list = []
        for br in obj.brand.all():
            list.append({'name': br.name, 'logo': br.get_absolute_url(), 'site': br.site})
        return list


class ProductSerializerForRelated(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    discountPersent = serializers.SerializerMethodField()
    productfield_id = serializers.SerializerMethodField()
    productfeature_id = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'productfield_id',
            'productfeature_id',
            'name',
            'price',
            'discount_price',
            'image',
            'discountPersent'
        )

    def get_productfield_id(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('-price').first()
        if products:
            return products.field.id

    def get_productfeature_id(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('-price').first()
        if products:
            return products.id

    def get_discountPersent(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('-price').first()
        if products:
            return products.field.discountPersent

    def get_discount_price(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('-price').first()
        if products:
            return products.get_price_after_discount_and_taxation()

    def get_price(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('-price').first()
        if products:
            return products.get_price()

    def get_image(self, obj):
        return obj.get_absolute_url()


class VisitedProductSerializer(serializers.ModelSerializer):
    product = ProductSerializerForRelated()

    class Meta:
        model = Visited
        fields = '__all__'


class FavoriteProductSerializerForGetFavoriteList(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteProduct
        fields = '__all__'

    def get_product(self, obj):
        product = Product.objects.get(pk=obj.product.id)
        serializer = ProductSerializerForAllProduct(product)
        return serializer.data


class ProductSerializerForAllProduct(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    discountPersent = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    productField = serializers.SerializerMethodField()
    exist = serializers.SerializerMethodField()
    productFeature = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'productField', 'productFeature', 'exist', 'category', 'name', 'image', 'price', 'discount_price',
            'discountPersent')

    def get_productFeature(self, obj):
        field = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        if field:
            return field[0].id
        return None

    def get_exist(self, obj):
        str = ''
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        if products:
            if products[0].inventory:
                str = 'موجود'
            else:
                str = 'نا موجود'

        return str

    def get_productField(self, obj):
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        if products:
            return products[0].field.id
        return None

    def get_category(self, obj):
        return {
            'id': obj.category.id,
            'title': obj.category.title
        }

    def get_discountPersent(self, obj):
        list = []
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        for product in products:
            list.append({'productfeature_id': product.id, 'seller': product.field.seller.title,
                         'discount_persent': product.field.discountPersent})
        return list

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_price(self, obj):
        list = []
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        for product in products:
            list.append(
                {'productfeature_id': product.id, 'seller': product.field.seller.title, 'price': product.get_price()})
        return list

    def get_discount_price(self, obj):
        list = []
        products = ProductFieldFeaturesValue.objects.filter(field__product=obj).order_by('price')
        for product in products:
            list.append(
                {'productfeature_id': product.id, 'seller': product.field.seller.title,
                 'discount_price': product.get_price_after_discount_and_taxation()})
        return list


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    # exist = serializers.SerializerMethodField()
    spicialField = serializers.SerializerMethodField()
    related_seller = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    root_category = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        fields = (
            'id',
            'get_name',
            # 'exist',
            'image',
            'spicialField',
            'brand',
            'seller',
            'related_seller',
            'get_visit',
            'get_category',
            'root_category',
            'get_videoGallery',
            'get_imageGallery',
            'get_tag_list',
            'get_sendWayBySeller',
            'get_description',
            'get_summary',
            'sell_number',
            'comment_number',
            'get_like_number',
            'advocate_number',
            'get_count_offer_this_product',
        )

    # def get_exist(self, obj):
    #     objects = []
    #     field = ProductFieldFeaturesValue.objects.filter(field__product=obj.product).order_by('price').first()
    #     objects = {
    #         'id': field.id,
    #         'seller_name': field.field.seller.title,
    #         'seller_logo': field.field.seller.get_absolute_url(),
    #         'seller_id': field.field.seller.id,
    #         'warranty': field.field.seller.warranty.name if field.field.seller.warranty else '',
    #         'key': field.key.title,
    #         'value': field.value,
    #         'inventory': 'موجود' if field.inventory else 'ناموجود',
    #         'price': field.price,
    #         'discountPersent': field.field.discountPersent,
    #         'get_price_after_discount': field.get_price_after_discount(),
    #         'get_price_after_discount_and_taxation': field.get_price_after_discount_and_taxation(),
    #     }
    #     return objects

    def get_root_category(self, obj):
        try:
            if obj.product.category.parent.parent:
                return {
                    '1': {
                        'id': obj.product.category.parent.parent.id,
                        'title': str(obj.product.category.parent.parent)
                    },
                    '2': {
                        'id': obj.product.category.parent.id,
                        'title': str(obj.product.category.parent)
                    },
                    '3': {
                        'id': obj.product.category.id,
                        'title': str(obj.product.category)
                    }
                }
            if not obj.product.category.parent.parent and obj.product.category.parent:
                return {
                    '1': {
                        'id': obj.product.category.parent.id,
                        'title': str(obj.product.category.parent)
                    },
                    '2': {
                        'id': obj.product.category.id,
                        'title': str(obj.product.category)
                    },
                }
        except:
            if not obj.product.category.parent:
                return {
                    '1': {
                        'id': obj.product.category.id,
                        'title': str(obj.product.category)
                    }
                }

    def get_id(self, obj):
        return obj.product.id

    def get_brand(self, obj):
        try:
            product = Product.objects.get(name=obj.product.name)
        except Product.DoesNotExist:
            return ''
        return {'id': product.brand.id, 'name': product.brand.name, 'logo': product.brand.get_absolute_url()}

    def get_seller(self, obj):
        warranty = None
        target = ProductFieldFeaturesValue.objects.filter(field__product=obj.product).order_by('price').first()
        fields = ProductFieldFeaturesValue.objects.filter(field__seller=target.field.seller,
                                                          field__product=target.field.product).order_by('price')
        if fields[0].field.warranty:
            warranty = fields[0].field.warranty.name
        elif fields[0].field.seller.warranty:
            warranty = fields[0].field.seller.warranty.name
        else:
            warranty = None
        objects = {
            'seller_name': target.field.seller.title,
            'seller_logo': target.field.seller.get_absolute_url(),
            'seller_id': target.field.seller.id,
            'warranty': None,
            'field_id': target.field.id,
            'variety_product': []
        }
        for field in fields:
            objects['warranty'] = warranty
            if field.inventory:
                objects['variety_product'].append(
                    {
                        'field_feature_id': field.id,
                        'name': field.field.product.name,
                        'key': field.key.title,
                        'value': field.value,
                        'inventory': 'موجود',
                        'price': field.price,
                        'discountPersent': field.field.discountPersent,
                        'get_price_after_discount': field.get_price_after_discount(),
                        'get_price_after_discount_and_taxation': field.get_price_after_discount_and_taxation(),
                    }
                )

        return objects

    def get_related_seller(self, obj):
        target = ProductFieldFeaturesValue.objects.filter(field__product=obj.product).order_by('price').first()
        fields = ProductFieldFeaturesValue.objects.filter(field__product=obj.product)
        objects = []
        for index, field in enumerate(fields):
            if field.inventory and field.field.seller != target.field.seller:
                if not objects:
                    objects.append(
                        {
                            'seller_name': None,
                            'seller_logo': None,
                            'seller_id': None,
                            'warranty': None,
                            'field_id': None,
                            'variety_product': []
                        }
                    )
                    if field.field.warranty:
                        warranty = field.field.warranty.name
                    elif field.field.seller.warranty:
                        warranty = field.field.seller.warranty.name
                    else:
                        warranty = None
                    objects[0]['seller_name'] = field.field.seller.title
                    objects[0]['seller_logo'] = field.field.seller.get_absolute_url()
                    objects[0]['seller_id'] = field.field.seller.id
                    objects[0]['warranty'] = warranty
                    objects[0]['field_id'] = field.field.id
                    objects[0]['variety_product'].append({
                        'field_feature_id': field.id,
                        'name': field.field.product.name,
                        'sendWayBySeller': field.field.get_sendWayBySeller(),
                        'price': field.price if field else None,
                        'key': field.key.title,
                        'value': field.value,
                        'inventory': 'موجود',
                        'discountPersent': field.field.discountPersent,
                        'discount_price': field.get_price_after_discount() if field else None,
                        'get_price_after_discount_and_taxation': field.get_price_after_discount_and_taxation()
                    })
                else:
                    if objects[len(objects) - 1]['seller_name'] == field.field.seller.title:
                        objects[len(objects) - 1]['variety_product'].append({
                            'field_feature_id': field.id,
                            'name': field.field.product.name,
                            'sendWayBySeller': field.field.get_sendWayBySeller(),
                            'price': field.price if field else None,
                            'key': field.key.title,
                            'value': field.value,
                            'inventory': 'موجود',
                            'discountPersent': field.field.discountPersent,
                            'discount_price': field.get_price_after_discount() if field else None,
                            'get_price_after_discount_and_taxation': field.get_price_after_discount_and_taxation()
                        })
                    else:
                        objects.append(
                            {
                                'seller_name': None,
                                'seller_logo': None,
                                'seller_id': None,
                                'warranty': None,
                                'field_id': None,
                                'variety_product': []
                            }
                        )
                        if field.field.warranty:
                            warranty = field.field.warranty.name
                        elif field.field.seller.warranty:
                            warranty = field.field.seller.warranty.name
                        else:
                            warranty = None
                        objects[len(objects) - 1]['seller_name'] = field.field.seller.title
                        objects[len(objects) - 1]['seller_logo'] = field.field.seller.get_absolute_url()
                        objects[len(objects) - 1]['seller_id'] = field.field.seller.id
                        objects[len(objects) - 1]['warranty'] = warranty
                        objects[len(objects) - 1]['field_id'] = field.field.id
                        objects[len(objects) - 1]['variety_product'].append({
                            'field_feature_id': field.id,
                            'name': field.field.product.name,
                            'sendWayBySeller': field.field.get_sendWayBySeller(),
                            'price': field.price if field else None,
                            'key': field.key.title,
                            'value': field.value,
                            'inventory': 'موجود',
                            'discountPersent': field.field.discountPersent,
                            'discount_price': field.get_price_after_discount() if field else None,
                            'get_price_after_discount_and_taxation': field.get_price_after_discount_and_taxation()
                        })

        return objects

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_spicialField(self, obj):
        list = []
        product = Product.objects.get(id=obj.product.id)
        for spicialField in ProductSpicialField.objects.filter(product=product):
            list.append({'key': spicialField.spicialField.spicialField.key, 'value': spicialField.spicialField.value})
        return list


class FavoriteProductListSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = FavoriteProduct
        fields = '__all__'


class ProductSerializerForComments(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category = CategorySerializerForListProduct()
    brand = BrandOfSellerSerializer()
    spicialField = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('name', 'category', 'brand', 'image', 'spicialField')

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_spicialField(self, obj):
        list = []
        for spicialField in ProductSpicialField.objects.filter(product=obj):
            list.append({'key': spicialField.spicialField.spicialField.key, 'value': spicialField.spicialField.value})
        return list


class ProductSerializerForComparision(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    category = CategorySerializerForListProduct()
    brand = BrandOfSellerSerializer()
    spicialField = serializers.SerializerMethodField()
    product_seller = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'description', 'summary', 'product_seller', 'like_number', 'brand', 'image',
                  'spicialField')

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_product_seller(self, obj):
        list = []
        fields = ProductField.objects.filter(product=obj)
        for field in fields:
            fi = ProductFieldFeaturesValue.objects.filter(field=field).order_by('-price').first()
            list.append({'name': field.seller.title, 'price': fi.price})
        return list

    def get_spicialField(self, obj):
        list = []
        for spicialField in ProductSpicialField.objects.filter(product=obj):
            list.append({'key': spicialField.spicialField.spicialField.key, 'value': spicialField.spicialField.value})
        return list


class SubCategorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'product', 'icon')

    def get_icon(self, obj):
        if obj.icon:
            return obj.get_absolute_url()
        return ''

    def get_product(self, obj):
        list = []
        objects = Product.objects.filter(Q(category=obj) & Q(adminConfirm=True))
        for object in objects:
            field = ProductFieldFeaturesValue.objects.filter(field__product=object, field__adminConfirm=True).order_by(
                '-price').first()
            list.append({
                'id': object.id,
                'productfield_id': field.field.id if field else None,
                'productfeature_id': field.id if field else None,
                'name': object.name,
                'price': field.price if field else None,
                'rate': field.field.get_rate() if field else None,
                'image': object.get_absolute_url(),
                'comment_number': field.field.comment_number if field else None,
            })
        return list


class CategorySerializerForSearchInCategory(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'icon')

    def get_icon(self, obj):
        return obj.get_absolute_url()


class CategorySerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'title', 'product', 'icon')

    def get_icon(self, obj):
        if obj.icon:
            return obj.get_absolute_url()
        return ''

    def get_product(self, obj):
        list = []
        objects = Product.objects.filter(
            Q(category=obj) | Q(category__parent=obj) | Q(category__parent__parent=obj)).filter(adminConfirm=True)
        for object in objects:
            field = ProductFieldFeaturesValue.objects.filter(field__product=object, field__adminConfirm=True).order_by(
                '-price').first()
            list.append({
                'id': object.id,
                'productfield_id': field.field.id if field else None,
                'productfeature_id': field.id if field else None,
                'name': object.name,
                'price': field.price if field else None,
                'rate': field.field.get_rate() if field else None,
                'image': object.get_absolute_url(),
                'comment_number': field.field.comment_number if field else None,
            })
        return list


class SellerSerializer(serializers.ModelSerializer):
    brand = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    state_limit = serializers.SerializerMethodField()
    city_limit = serializers.SerializerMethodField()
    warranty = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        exclude = ('mobile',)

    def get_warranty(self, obj):
        return {
            'name': obj.warranty.name,
            'month': obj.warranty.month
        }

    def get_state_limit(self, obj):
        return {
            'id': obj.state.id,
            'title': obj.state.name
        }

    def get_city_limit(self, obj):
        return {
            'id': obj.city.id,
            'title': obj.city.name
        }

    def get_logo(self, obj):
        return obj.get_absolute_url()

    def get_brand(self, obj):
        list = []
        for br in obj.brand.all():
            list.append({'name': br.name, 'logo': br.get_absolute_url(), 'site': br.site})
        return list

    def get_category(self, obj):
        list = []
        for category in obj.category.all():
            list.append({'title': category.title, 'id': category.id})
        return list


class ProductOfSellerSerializer(serializers.ModelSerializer):
    brand = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ('title', 'logo', 'brand', 'address', 'code', 'products')

    def get_brand(self, obj):
        list = []
        for br in obj.brand.all():
            list.append({'name': br.name, 'logo': br.get_absolute_url(), 'site': br.site})
        return list

    def get_products(self, obj):
        list = []
        for br in obj.brand.all():
            products = Product.objects.filter(brand=br, adminConfirm=True)
            for product in products:
                if product not in list:
                    list.append(product)
        serializer = ProductSerializerForRelated(list, many=True)
        return serializer.data

    def get_logo(self, obj):
        return obj.get_absolute_url()


class SellerSerializerForList(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ('id', 'title', 'logo', 'code')

    def get_logo(self, obj):
        return obj.get_absolute_url()


class ProductSerializerForCommentsList(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductField
        fields = ('id', 'name', 'image')

    def get_image(self, obj):
        return obj.product.get_absolute_url()

    def get_name(self, obj):
        return obj.product.name


class ProductSerializerForSearch(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    productField_id = serializers.SerializerMethodField()
    product_id = serializers.SerializerMethodField()
    exist = serializers.SerializerMethodField()
    productFeature_id = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    discountPersent = serializers.SerializerMethodField()
    discount_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    price_with_taxation = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductFieldFeaturesValue
        fields = (
            'product_id',
            'productField_id',
            'productFeature_id',
            'exist',
            'seller',
            'brand',
            'category',
            'name',
            'image',
            'price',
            'price_with_taxation',
            'discount_price',
            'discountPersent')

    def get_productFeature_id(self, obj):
        return obj.id

    def get_product_id(self, obj):
        return obj.field.product.id

    def get_name(self, obj):
        return obj.field.product.name

    def get_exist(self, obj):
        if obj.inventory:
            str = 'موجود'
        else:
            str = 'نا موجود'
        return str

    def get_productField_id(self, obj):
        return obj.field.id

    def get_category(self, obj):
        return obj.field.product.category.title

    def get_image(self, obj):
        return obj.field.product.get_absolute_url()

    def get_seller(self, obj):
        return obj.field.seller.title

    def get_brand(self, obj):
        return obj.field.product.brand.name

    def get_discountPersent(self, obj):
        return obj.field.discountPersent

    def get_price(self, obj):
        return obj.get_price()

    def get_price_with_taxation(self, obj):
        return obj.get_price_after_taxation()

    def get_discount_price(self, obj):
        return obj.get_price_after_discount_and_taxation()
