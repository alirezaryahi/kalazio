import math

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.html import format_html
from django_jalali.db import models as jmodels

import adminPanel.models
from brand.models import Brand
from kavenegar import *
from tinymce.models import HTMLField
from django.template.defaultfilters import truncatechars
from django.conf import settings

kave_api = KavenegarAPI('65456F4B654B4146357A54497A4B546A6F43414F384D7572537254484B395838')

# Create your models here.

number_rate = (
    ('5', 'عالی'),
    ('4', 'خوب'),
    ('3', 'معمولی'),
    ('2', 'بد'),
    ('1', 'خیلی بد'),
)


class SpicialField(models.Model):
    key = models.CharField(max_length=500, verbose_name='نام ویژگی', unique=True)
    description = models.TextField(verbose_name='توضیحات', blank=True, null=True)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = 'کلید مشخصه ویژه هر محصول'
        verbose_name_plural = 'کلید های مشخصات ویژه هر محصول'


class ProductSpicialField(models.Model):
    spicialField = models.ForeignKey('SpicialFieldValue', on_delete=models.CASCADE, verbose_name='نام ویژگی')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='محصول', blank=True, null=True,
                                related_name='productspicial')

    def __str__(self):
        return self.spicialField.value

    def clean(self):
        objects = ProductSpicialField.objects.all()
        for obj in objects:
            if obj.spicialField == self.spicialField and obj.product == self.product:
                raise ValidationError('محصول با این مشخصه وجود دارد')

    class Meta:
        verbose_name = 'ویژگی هر محصول'
        verbose_name_plural = 'ویژگی های محصولات'


class CategorySpicialField(models.Model):
    spicialField = models.ForeignKey('SpicialFieldValue', on_delete=models.CASCADE, verbose_name='نام ویژگی')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name='دسته بندی', blank=True, null=True,
                                 related_name='categoryspicial')

    def __str__(self):
        return self.spicialField.value

    def clean(self):
        objects = CategorySpicialField.objects.all()
        for obj in objects:
            if obj.spicialField == self.spicialField and obj.category == self.category:
                raise ValidationError('دسته بندی با این مشخصه وجود دارد')

    class Meta:
        verbose_name = 'ویژگی هر دسته بندی'
        verbose_name_plural = 'ویژگی های دسته بندی ها'


class SpicialFieldValue(models.Model):
    spicialField = models.ForeignKey(SpicialField, on_delete=models.CASCADE, verbose_name='نام ویژگی',
                                     related_name='spicialField')
    value = models.CharField(max_length=500, verbose_name='مقدار ویژگی')

    def __str__(self):
        return str(f'{self.value} --> {self.spicialField.key}')

    class Meta:
        verbose_name = 'مقدار مشخصه ویژه'
        verbose_name_plural = 'مقدار های مشخصات ویژه'


class Category(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, on_delete=models.SET_NULL,
                               related_name='children', verbose_name='زیر دسته')
    title = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='category_icon/', verbose_name='آیکن', blank=True, null=True)
    commission = models.FloatField(default=0.0, verbose_name='درصد کمیسون')
    advocate = models.BooleanField(default=False, verbose_name='پر طرفدار')

    class Meta:
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'
        ordering = ['parent__id']

    def get_absolute_url(self):
        if self.icon:
            return settings.SITE_URI + '{path}'.format(path=self.icon.url)
        return ''

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    image = models.ImageField(upload_to='product_image/', verbose_name='تصویر')

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.image.url)

    class Meta:
        verbose_name = 'تصویر'
        verbose_name_plural = 'تصاویر'


class GalleryVideo(models.Model):
    video = models.FileField(upload_to='product_video/', verbose_name='فیلم')

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.video.url)

    class Meta:
        verbose_name = 'فیلم'
        verbose_name_plural = 'فیلم ها'


class Warranty(models.Model):
    name = models.CharField(max_length=300, blank=True, null=True, verbose_name='نام گارانتی')
    month = models.IntegerField(default=0, verbose_name='تعداد ماه')

    class Meta:
        verbose_name = 'گارانتی'
        verbose_name_plural = 'گارانتی ها'

    def __str__(self):
        return self.name


rate_choices = (
    ('1', 1),
    ('2', 2),
    ('3', 3),
    ('4', 4),
    ('5', 5),
)


class Evidence(models.Model):
    title = models.CharField(max_length=200, verbose_name='نام مدرک')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'مدرک'
        verbose_name_plural = 'مدارک'


evidenceConfirm = (
    ('waiting', 'در دست بررسی'),
    ('Confirmation', 'تایید'),
)


class UserEvidence(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر')
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, verbose_name='مدرک')
    file = models.FileField(upload_to='private/evidence_user_file/', verbose_name='فایل اپلود شده')
    evidenceConfirm = models.CharField(max_length=30, default='waiting', choices=evidenceConfirm, verbose_name='وضعیت')

    def __str__(self):
        return self.user.username

    def get_absolute_file(self):
        if self.file:
            return settings.SITE_URI + '{path}'.format(path=self.file.url)
        return ''

    # Get evidence confirm display
    def get_evidenceConfirm(self):
        return self.get_evidenceConfirm_display()

    class Meta:
        verbose_name = 'مدرک کاربر'
        verbose_name_plural = 'مدارک کاربران'


class Product(models.Model):
    name = models.CharField(max_length=500, verbose_name='نام محصول')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='برند محصول', blank=True, null=True)
    image = models.ImageField(upload_to='products/', verbose_name='تصویر', blank=True, null=True)
    imageGallery = models.ManyToManyField(GalleryImage, blank=True, verbose_name='گالری تصاویر',
                                          related_name='imageGallery')
    videoGallery = models.ManyToManyField(GalleryVideo, blank=True, verbose_name='گالری فیلم ها',
                                          related_name='videoGallery')
    evidence = models.ManyToManyField(Evidence, blank=True, verbose_name='مدارک مورد نیاز', related_name='evidence')
    description = HTMLField(verbose_name='نقد و بررسی', blank=True, null=True)
    summary = models.TextField(verbose_name='توضیحات مختصر', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='دسته بندی', blank=True, null=True)
    product_seller = models.ManyToManyField('Seller', verbose_name='فروشنده های محصول', blank=True)
    like_number = models.IntegerField(verbose_name='تعداد لایک', default=0)
    tags = models.CharField(max_length=300, verbose_name='کلمات کلیدی', blank=True, null=True)
    visit = models.IntegerField(default=0, verbose_name='تعداد بازدید')
    weight = models.FloatField(default=0.0, verbose_name='وزن')
    length = models.FloatField(default=0.0, verbose_name='طول')
    width = models.FloatField(default=0.0, verbose_name='عرض')
    height = models.FloatField(default=0.0, verbose_name='ارتفاع')
    adminConfirm = models.BooleanField(default=False, verbose_name='تایید توسط ادمین')

    def __str__(self):
        return f'{self.name} ({self.brand})'

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)

    def tag_list(self):
        return self.tags.split(',')

    def get_absolute_url(self):
        if self.image:
            return settings.SITE_URI + '{path}'.format(path=self.image.url)
        return ''

    tag_list.short_description = 'کلمات کلیدی'

    def save(self, *args, **kwargs):
        self.advocate_number = self.visit + self.like_number
        self.tags = f'{self.name},{self.category}, {self.brand}'
        return super(Product, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'


class RateProduct(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر', related_name='rateUser')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول',
                                related_name='rateProduct', blank=True, null=True)
    product_seller = models.ForeignKey('Seller', on_delete=models.CASCADE, verbose_name='فروشنده محصول')
    rate = models.CharField(max_length=10, default=0, choices=rate_choices, blank=True, null=True,
                            verbose_name='امتیاز')

    class Meta:
        verbose_name = 'امتیاز محصول'
        verbose_name_plural = 'امتیاز محصولات'

    def __str__(self):
        return self.rate


class FavoriteProduct(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر', related_name='favoriteUser')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول')

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = 'محصول مورد علاقه'
        verbose_name_plural = 'محصولات مورد علاقه'


class Visited(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر', related_name='visitUser')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول', blank=True, null=True)

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'محصول مشاده شده کاربر'
        verbose_name_plural = 'محصولات مشاهده شده کاربران'


send_pay = (
    ('customer', 'پرداخت توسط مشتری'),
    ('seller', 'پرداخت توسط فروشنده')
)

payment_method = (
    ('direct', 'مستقیم'),
    ('installment', 'قسطی'),
    ('both', 'هردو'),
)


class Seller(models.Model):
    logo = models.ImageField(upload_to='seller_logo/', verbose_name='لوگوی فروشنده')
    title = models.CharField(max_length=500, verbose_name='نام فروشگاه')
    code = models.IntegerField(verbose_name='کد فروشنده', blank=True, null=True)
    feature = models.BooleanField(default=False, verbose_name='فروشنده برگزیده')
    payment_method = models.CharField(choices=payment_method, max_length=100, verbose_name='روش پرداخت',
                                      default='direct')
    warranty_status = models.BooleanField(default=False, verbose_name='گارانتی')
    warranty = models.ForeignKey(Warranty, on_delete=models.CASCADE, verbose_name='وضعیت گارانتی', blank=True,
                                 null=True, related_name='sellerWarranty')
    sellerRepresentative = models.ForeignKey('adminPanel.SellerRepresentative', on_delete=models.CASCADE,
                                             verbose_name='نماینده فروشنده', blank=True, null=True,
                                             related_name='sellerrep')
    name = models.CharField(max_length=100, verbose_name='نام رسمی و ثبتی شرکت', blank=True, null=True)
    registrationId = models.CharField(max_length=30, verbose_name='شناسه ثبت', blank=True, null=True)
    melliId = models.CharField(max_length=30, verbose_name='شناسه ملی', blank=True, null=True)
    companyEmail = models.EmailField(verbose_name='ایمیل شرکت', blank=True, null=True)
    shebaNumber = models.CharField(max_length=100, verbose_name='شماره شبا', blank=True, null=True)
    bank = models.CharField(max_length=100, verbose_name='بانک', blank=True, null=True)
    accountOwner = models.CharField(max_length=100, verbose_name='نام صاحب حساب', blank=True, null=True)
    accountNumber = models.CharField(max_length=100, verbose_name='شماره حساب', blank=True, null=True)
    taxationAccountNumber = models.CharField(max_length=100, verbose_name='شماره حساب واریز مالیات', blank=True,
                                             null=True)
    restore_status = models.BooleanField(default=False, verbose_name='بازگردانی')
    restore = models.TextField(verbose_name='وضعیت بازگردانی', blank=True, null=True)
    date_joined = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ عضویت')
    sendWay = models.BooleanField(default=False, verbose_name='ارسال توسط فروشنده')
    payBySeller = models.BooleanField(default=False, verbose_name='هزینه ارسال توسط فروشنده')
    state_limit = models.ManyToManyField('order.State', verbose_name='محدودیت ارسال به استان ها', blank=True,
                                         related_name='stateLimit')
    city_limit = models.ManyToManyField('order.City', verbose_name='محدودیت ارسال به شهرستان ها', blank=True,
                                        related_name='cityLimit')
    phone = models.CharField(max_length=11, verbose_name='تلفن')
    longitude = models.CharField(max_length=1000, default='', verbose_name='طول جغرافیایی', blank=True, null=True)
    latitude = models.CharField(max_length=1000, default='', verbose_name='عرض جغرافیایی', blank=True, null=True)
    mobile_regex = RegexValidator(regex=r'^(09)\d{9}$',
                                  message="باید با 09 شروع شده و 12 رقم باشد")
    mobile = models.CharField(max_length=12, validators=[mobile_regex], verbose_name='موبایل')
    brand = models.ManyToManyField(Brand, blank=True, verbose_name='برند ها')
    category = models.ManyToManyField(Category, blank=True, verbose_name='دسته بندی ها')
    state = models.ForeignKey('order.State', verbose_name='استان', on_delete=models.CASCADE, blank=True, null=True)
    city = models.ForeignKey('order.City', verbose_name='شهر', on_delete=models.CASCADE, blank=True, null=True)
    commission = models.FloatField(default=0.0, verbose_name='درصد کمیسون')
    address = models.TextField(verbose_name='ادرس دقیق')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'فروشگاه عرضه کننده محصول'
        verbose_name_plural = 'فروشگاه های عرضه کننده محصول'

    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.logo.url)

    # Get payment method display
    def get_payment_method(self):
        return self.get_payment_method_display()


class ProductField(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول', related_name='productField')
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, verbose_name='فروشنده')
    warranty = models.ForeignKey(Warranty, on_delete=models.CASCADE, verbose_name='وضعیت گارانتی', blank=True,
                                 null=True, related_name='ProductFieldWarranty')
    discountPersent = models.IntegerField(default=0, verbose_name='درصد تخفیفی')
    commission = models.FloatField(default=0.0, verbose_name='درصد کمیسون')
    maxBuy = models.IntegerField(verbose_name='محدودیت تعداد خرید', blank=True, null=True)
    maxTime = models.IntegerField(verbose_name='محدودیت زمانی خرید', blank=True, null=True)
    taxation = models.BooleanField(default=False, verbose_name='مالیات بر ارزش افزوده')
    confirm = models.BooleanField(default=False, verbose_name='تایید توسط فروشنده هنگام خرید')
    adminConfirm = models.BooleanField(default=False, verbose_name='تایید توسط ادمین')
    specialoffer = models.BooleanField(default=False, verbose_name='پیشنهاد ویزه')
    sell_number = models.IntegerField(verbose_name='تعداد فروش', default=0)
    comment_number = models.IntegerField(verbose_name='تعداد نظرات', default=0)
    buy_users = models.ManyToManyField('user.User', verbose_name='خریداران', blank=True)
    advocate_number = models.IntegerField(verbose_name='امتیاز', default=0)

    class Meta:
        verbose_name = 'مشخصات محصول'
        verbose_name_plural = 'مشخصات محصولات'

    def __str__(self):
        return self.product.name + ' ' + f'({self.seller}) ({self.product.brand})'

    def get_name(self):
        return self.product.name

    def get_brand(self):
        return self.product.brand.name

    def get_absolute_url(self):
        if self.product.image:
            return settings.SITE_URI + '{path}'.format(path=self.product.image.url)
        return ''

    def get_visit(self):
        return self.product.visit

    def get_category(self):
        return self.product.category.title

    def get_summary(self):
        if self.product.summary:
            return self.product.summary
        else:
            return truncatechars(self.product.description, 100)

    def get_videoGallery(self):
        list = []
        objects = self.product.videoGallery.all()
        for object in objects:
            list.append(object.get_absolute_url())
        return list

    def get_imageGallery(self):
        list = []
        objects = self.product.imageGallery.all()
        for object in objects:
            list.append(object.get_absolute_url())
        return list

    def get_tag_list(self):
        return str(self.product.tag_list())

    def get_like_number(self):
        return self.product.like_number

    def get_description(self):
        return self.product.description

    def get_warranty(self):
        if self.seller.warranty:
            return self.seller.warranty.name
        if self.warranty:
            return self.warranty.name
        return ''

    def get_sendWayBySeller(self):
        return self.seller.sendWay

    def get_product_seller(self):
        return self.seller.title

    def get_rate(self):
        num = 0
        for rate in self.product.rateProduct.all():
            if rate:
                num += int(rate.rate)
        if num > 0:
            num = num / len(self.rateProduct.all())
        num += len(self.comment_set.all())
        return num

    def get_count_offer_this_product(self):
        count = 0
        num = 0
        persent = 0
        for comment in self.comment_set.all():
            if comment:
                num += 1
                if comment.suggest == 'suggest':
                    count += 1
        if count and num:
            persent = (num / count) * 100
        return {
            'count-offer': count,
            'persent-offer': persent
        }


class ProductFieldFeaturesKey(models.Model):
    title = models.CharField(max_length=300, verbose_name='مشخصه محصول')

    def __str__(self):
        return self.title


class ProductFieldFeaturesValue(models.Model):
    field = models.ForeignKey(ProductField, on_delete=models.CASCADE, verbose_name='مشخصه محصول')
    key = models.ForeignKey(ProductFieldFeaturesKey, on_delete=models.CASCADE, verbose_name='عنوان', blank=True,
                            null=True)
    value = models.CharField(max_length=300, verbose_name='مقدار', blank=True, null=True)
    inventory = models.IntegerField(default=0, blank=True, null=True, verbose_name='تعداد موجودی')
    price = models.FloatField(default=0.0, verbose_name='قیمت')

    def __str__(self):
        return self.field.product.name

    def sell_number(self, obj):
        return self.field.sell_number

    # Get prices with discounts and taxes
    def get_price_after_discount_and_taxation(self):
        price = 0
        if self.field.discountPersent > 0:
            price = self.price - ((self.price * self.field.discountPersent) / 100)
        if self.field.taxation and price > 0:
            price += (price * 9) / 100
        if self.field.taxation and price == 0:
            price = self.price + ((self.price * 9) / 100)
        if not self.field.discountPersent and not self.field.taxation:
            price = self.price
        return math.ceil(price)

    get_price_after_discount_and_taxation.short_description = 'قیمت'

    def save(self, *args, **kwargs):
        p = self.get_price_after_discount_and_taxation()
        pp = p - ((p * self.field.commission) / 100)
        seller = self.field.seller
        if seller not in self.field.product.product_seller.all():
            self.field.product.product_seller.add(seller)
            self.field.product.save()
        return super(ProductFieldFeaturesValue, self).save(*args, **kwargs)

    # Amount of commission
    def get_commision_price(self):
        commision = 0
        tax = 0
        price = math.ceil(self.price)
        if self.field.taxation:
            tax = math.ceil(((price * 9) / 100))
        if self.field.commission:
            commision = math.ceil(((price * self.field.commission) / 100))
        return {
            'tax': tax,
            'commision': commision
        }

    def get_price(self):
        return math.ceil(self.price)

    # Get price with taxation
    def get_price_after_taxation(self):
        price = 0
        if self.field.taxation and price > 0:
            price += (price * 9) / 100
        elif self.field.taxation and price == 0:
            price = self.price + ((self.price * 9) / 100)
        elif not self.field.taxation:
            price = self.price
        return math.ceil(price)

    # Get price with discount
    def get_price_after_discount(self):
        price = self.get_price()
        if self.field.discountPersent > 0:
            price = self.price - ((self.price * self.field.discountPersent) / 100)
        return math.ceil(price)

    get_price_after_discount.short_description = 'قیمت(با احتساب تخفیف و بدون مالیات)'
