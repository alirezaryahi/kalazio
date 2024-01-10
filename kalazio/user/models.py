from django.db import models
from django_jalali.db import models as jmodels
from comments.models import Comment
from questionAndAnswer.models import QuestionAndAnswer
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import time

# Create your models here.

level = (
    ('low', 'کم'),
    ('medium', 'متوسط'),
    ('important', 'زیاد')
)


class Notifications(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='کاربر', related_name='notiUser')
    title = models.CharField(max_length=300, verbose_name='عنوان پیام')
    date = jmodels.jDateField(auto_now_add=True, verbose_name='تاریخ پیام')
    content = models.TextField(verbose_name='متن پیام')
    level = models.CharField(max_length=20, choices=level, verbose_name='اولویت')

    def __str__(self):
        return str(self.user.id)

    def get_level(self):
        return self.get_level_display()

    get_level.short_description = 'اولویت'

    class Meta:
        verbose_name = 'اطلاع رسانی'
        verbose_name_plural = 'اطلاع رسانی ها'


class Gift(models.Model):
    serial = models.CharField(max_length=100, verbose_name='سریال')
    amount = models.FloatField(verbose_name='مبلغ')
    orderCode = models.ForeignKey('order.Order', verbose_name='کد سفارش', blank=True, null=True,
                                  on_delete=models.CASCADE, related_name='giftOrder')
    donator = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='اهدا کننده', related_name='donator')
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='استفاده کننده', blank=True, null=True,
                             related_name='giftUser')
    use = models.BooleanField(default=False, verbose_name='استفاده شده / نشده')

    def __str__(self):
        return self.serial

    class Meta:
        verbose_name = 'کارت هدیه'
        verbose_name_plural = 'کارت های هدیه'


gender = (
    ('male', 'مرد'),
    ('female', 'زن')
)

role = (
    ('user', 'عضو یاشگاه'),
    ('brandRepresentative', 'نماینده برند'),
    ('sellerRepresentative', 'نماینده فروشنده'),
)

shahkar = (
    ('confirm', 'احراز شده'),
    ('deny', 'عدم تطابق شماره ملی با تلفن همراه'),
    ('pending', 'احراز نشده'),
)


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=role, default='')
    username = models.CharField(max_length=11, verbose_name='تلفن', unique=True)
    email = models.EmailField(max_length=100, verbose_name='ایمیل', unique=True, blank=True, null=True)
    phone = models.CharField(max_length=11, verbose_name='تلفن ثابت', blank=True, null=True)
    newsletters = models.BooleanField(default=False, verbose_name='وضعیت دریافت خبرنامه')
    date_joined = jmodels.jDateField(verbose_name='تاریخ عضویت', auto_now_add=True)
    first_name = models.CharField(max_length=100, verbose_name='نام', blank=True, null=True)
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=gender, verbose_name='جنسیت', blank=True, null=True)
    codeMelli = models.CharField(max_length=10, verbose_name='کد ملی', blank=True, null=True)
    register_number = models.IntegerField(default=0, verbose_name='دفعات رجیستر کد ملی')
    register_date = models.DateTimeField(blank=True, null=True)
    melliImage = models.ImageField(upload_to='private/melli_image/', verbose_name='عکس کارت ملی', blank=True, null=True)
    ibanNumber = models.CharField(max_length=40, verbose_name='شماره شبا', blank=True, null=True)
    cartNumber = models.CharField(max_length=40, verbose_name='شماره کارت', blank=True, null=True)
    dateOfBirth = jmodels.jDateField(verbose_name='سن', blank=True, null=True)
    address = models.TextField(verbose_name='ادرس', blank=True, null=True)
    walletBalance = models.FloatField(default=0.0, verbose_name='موجودی کیف پول')
    favoriteProduct = models.ManyToManyField('product.FavoriteProduct', verbose_name='لیست محصولات مورد علاقه',
                                             blank=True,
                                             related_name='favoriteProduct')
    comments = models.ManyToManyField(Comment, verbose_name='لیست نظرات', blank=True, related_name='comments')
    questionAndAnswer = models.ManyToManyField(QuestionAndAnswer, verbose_name='لیست پرسش ها و پاسخ ها', blank=True,
                                               related_name='questionAndAnswer')
    notifications = models.ManyToManyField(Notifications, verbose_name='لیست اطلاع رسانی ها', blank=True,
                                           related_name='notifications')
    gifts = models.ManyToManyField(Gift, verbose_name='لیست کارت های هدیه', blank=True,
                                   related_name='gifts')
    is_active = models.BooleanField(default=True, verbose_name='فعال / غیر فعال')
    join = models.BooleanField(default=False, verbose_name='رجیستر شده')
    authorized = models.CharField(max_length=100, default='', choices=shahkar, verbose_name='تایید هویت')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربر ها'

    # Get authorized display
    def get_authorized(self):
        return self.get_authorized_display()

    # Donated gift cards
    def get_gift_donate(self):
        list = []
        gifts = Gift.objects.filter(donator=self)
        for gift in gifts:
            list.append(gift)
        return list

    get_gift_donate.short_description = 'کارت های هدیه اهدا شده'

    # Received gift cards
    def get_gift_user(self):
        list = []
        gifts = Gift.objects.filter(user=self)
        for gift in gifts:
            list.append(gift)
        return list

    get_gift_user.short_description = 'کارت های هدیه دریافت شده'


class PhoneAuthenticated(models.Model):
    phone = models.CharField(max_length=11, verbose_name='تلفن')
    code = models.CharField(max_length=5, verbose_name='کد')
    created = models.FloatField(default=time.time, verbose_name='زمان')

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = 'کد احراز هویت موبایل'
        verbose_name_plural = 'کد های احراز هویت موبایل'


class Samava(models.Model):
    phone = models.CharField(max_length=11, verbose_name='تلفن', blank=True, null=True)
    access_token = models.CharField(max_length=600, blank=True, null=True, verbose_name='توکن')
    jti = models.CharField(max_length=200, blank=True, null=True, verbose_name='شمارنده یکتا')
    expires_in = models.IntegerField(default=0, verbose_name='مدت زمان ولید بودن به ثانیه')
    creation_time = models.CharField(max_length=100, null=True, blank=True, verbose_name='زمان ایجاد توکن')
    time = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='زمان')
    authorize_url = models.CharField(max_length=300, blank=True, null=True)
    b2b_base_url = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=32, blank=True, null=True)
    secure_code = models.CharField(max_length=200, blank=True, null=True)
    code = models.CharField(max_length=200, blank=True, null=True)
    count = models.IntegerField(default=0)
    expire = models.BooleanField(default=False)

    def __str__(self):
        return str(self.secure_code)

    class Meta:
        verbose_name = 'توکن سماوا'
        verbose_name_plural = 'سماوا'
