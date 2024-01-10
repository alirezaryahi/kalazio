from django.db import models
from django.conf import settings

# from product import models


# Create your models here.

rate_choices = (
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
)


class Brand(models.Model):
    logo = models.ImageField(upload_to='brand_logo/', verbose_name='لوگوی برند')
    name = models.CharField(max_length=300, verbose_name='نام برند')
    description = models.TextField(verbose_name='توضیحات')
    phone = models.CharField(max_length=11, verbose_name='تلفن')
    brandRepresentative = models.ForeignKey('adminPanel.BrandRepresentative', on_delete=models.CASCADE,
                                            verbose_name='نماینده برند', blank=True, null=True, related_name='brandrep')
    registrationId = models.CharField(max_length=30, verbose_name='شناسه ثبت', blank=True, null=True)
    melliId = models.CharField(max_length=30, verbose_name='شناسه ملی', blank=True, null=True)
    address = models.TextField(verbose_name='آدرس')
    site = models.URLField(max_length=1024, blank=True, verbose_name='لینک سایت')
    category = models.ManyToManyField('product.Category', blank=True, verbose_name='دسته بندی برند')
    brand_seller = models.ManyToManyField('product.Seller', blank=True, verbose_name='فروشنده های برند',
                                          related_name='brand_seller')
    tick = models.BooleanField(default=False, verbose_name='تیک تایید هویت')
    specialoffer = models.BooleanField(default=False, verbose_name='برند منتخب')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'برند'
        verbose_name_plural = 'برند ها'

    # Get average rate
    def get_average_rate(self):
        num = 0
        for rate in self.ratebrand_set.all():
            if rate:
                num += int(rate.rate)
        if num > 0:
            return num / len(self.ratebrand_set.all())
        return 0

    # Get url of logo field
    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.logo.url)


class RateBrand(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر', related_name='brandrateUser')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='محصول')
    rate = models.CharField(max_length=10, default=1, choices=rate_choices, blank=True, null=True,
                            verbose_name='امتیاز')

    class Meta:
        verbose_name = 'امتیاز محصول'
        verbose_name_plural = 'امتیاز محصولات'

    def __str__(self):
        return f'{self.user.last_name} {self.product} {self.rate}'


class VideoBanner(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='برند', blank=True, null=True)
    video = models.FileField(upload_to='banner_video/', verbose_name='فیلم')
    title = models.CharField(max_length=500, verbose_name='نام بنر')
    description = models.TextField(verbose_name='توضیحات', blank=True, null=True)
    link = models.URLField(max_length=1024, verbose_name='لینک فیلم', blank=True, null=True)

    def __str__(self):
        return self.brand.name

    class Meta:
        verbose_name = 'بنر ویدیویی'
        verbose_name_plural = 'بنر های ویدیویی'

    # Get url of video field
    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.video.url)


class ImageBanner(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='برند', blank=True, null=True)
    image = models.FileField(upload_to='banner_image/', verbose_name='عکس')
    title = models.CharField(max_length=500, verbose_name='نام بنر')
    description = models.TextField(verbose_name='توضیحات', blank=True, null=True)
    link = models.URLField(max_length=1024, verbose_name='لینک تصویر', blank=True, null=True)

    def __str__(self):
        return self.brand.name

    class Meta:
        verbose_name = 'بنر تصویری'
        verbose_name_plural = 'بنر های تصویری'

    # Get url of image field
    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.image.url)


typee = (
    ('vertical', 'عمودی'),
    ('horizontal', 'افقی'),
    ('big-top', 'بنر بزرگ بالا'),
    ('first-little-right-top', 'بنر کوچک راست بالا'),
    ('second-little-right-top', 'بنر دوم کوچک راست بالا'),
)


class Banner(models.Model):
    type = models.CharField(max_length=100, choices=typee, verbose_name='جایگاه')
    image = models.FileField(upload_to='banner_image_main_page/', verbose_name='عکس')
    title = models.CharField(max_length=500, verbose_name='عنوان', blank=True, null=True)
    description = models.TextField(verbose_name='توضیحات', blank=True, null=True)
    link = models.URLField(max_length=1024, verbose_name='لینک تصویر', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'بنر صفحه اصلی'
        verbose_name_plural = 'بنر های صفحه اصلی'

    # Get url of link field
    def get_absolute_url(self):
        return settings.SITE_URI + '{path}'.format(path=self.image.url)
