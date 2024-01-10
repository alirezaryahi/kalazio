from .models import Brand, ImageBanner, VideoBanner, Banner
from rest_framework import serializers
from product.models import Category, Seller


class BrandSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('description', 'phone', 'address', 'site')


class ImageBannerSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = ImageBanner
        fields = ('image', 'title', 'description', 'link')


class VideoBannerSerializerForEdit(serializers.ModelSerializer):
    class Meta:
        model = VideoBanner
        fields = ('video', 'title', 'description', 'link')


class ImageBannerSerializerForGet(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    class Meta:
        model = ImageBanner
        fields = ('image', 'brand', 'title', 'description', 'link')

    def get_image(self, obj):
        return obj.get_absolute_url()

    def get_brand(self, obj):
        return obj.brand.name


class VideoBannerSerializerForGet(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    class Meta:
        model = VideoBanner
        fields = ('video', 'brand', 'title', 'description', 'link')

    def get_video(self, obj):
        return obj.get_absolute_url()

    def get_brand(self, obj):
        return obj.brand.name


class CategorySerializerForListProduct(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title')


class ImageBannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    class Meta:
        model = ImageBanner
        exclude = ('id',)

    def get_brand(self, obj):
        return obj.brand.name

    def get_image(self, obj):
        return obj.get_absolute_url()


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = '__all__'

    def get_image(self, obj):
        return obj.get_absolute_url()


class VideoBannerSerializer(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()

    class Meta:
        model = VideoBanner
        fields = '__all__'

    def get_video(self, obj):
        return obj.get_absolute_url()


class SellerBrandSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Seller
        fields = ('title', 'logo', 'code', 'state', 'city', 'address')

    def get_logo(self, obj):
        return obj.get_absolute_url()


class BrandOfSellerSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'logo', 'name')

    def get_logo(self, obj):
        return obj.get_absolute_url()


class BrandSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    brand_seller = serializers.SerializerMethodField()
    imageBanner = serializers.SerializerMethodField()
    videoBanner = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = '__all__'

    def get_logo(self, obj):
        return obj.get_absolute_url()

    def get_category(self, obj):
        list = []
        brands = Brand.objects.all()
        for brand in brands:
            for cat in brand.category.all():
                if cat not in list:
                    list.append(cat)
        serializer = CategorySerializerForListProduct(list, many=True)
        return serializer.data

    def get_brand_seller(self, obj):
        list = []
        brands = Brand.objects.all()
        for brand in brands:
            for seller in brand.brand_seller.all():
                if seller not in list:
                    list.append(seller)
        serializer = SellerBrandSerializer(list, many=True)
        return serializer.data

    def get_imageBanner(self, obj):
        ibanner = ImageBanner.objects.filter(brand=obj)
        serializer = ImageBannerSerializer(ibanner, many=True)
        return serializer.data

    def get_videoBanner(self, obj):
        vbanner = VideoBanner.objects.filter(brand=obj)
        serializer = VideoBannerSerializer(vbanner, many=True)
        return serializer.data


class BrandSerializerForList(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'name', 'logo', 'site', 'phone', 'get_average_rate')

    def get_logo(self, obj):
        return obj.get_absolute_url()


class BrandSerializerForImageBanner(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    imageBanner = serializers.SerializerMethodField()
    vidoeBanner = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'name', 'logo', 'description', 'imageBanner', 'vidoeBanner')

    def get_logo(self, obj):
        return obj.get_absolute_url()

    def get_imageBanner(self, obj):
        ibanner = ImageBanner.objects.filter(brand=obj)
        serializer = ImageBannerSerializer(ibanner, many=True)
        return serializer.data

    def get_vidoeBanner(self, obj):
        vbanner = VideoBanner.objects.filter(brand=obj)
        serializer = VideoBannerSerializerForGet(vbanner, many=True)
        return serializer.data
