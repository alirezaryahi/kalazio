from django.db.models.signals import post_save, pre_save, post_init
from user.models import User, Gift
from django.db import models
from product.models import Product, Warranty, Seller, ProductField, ProductFieldFeaturesValue
from django_jalali.db import models as jmodels
import jdatetime
import uuid
from datetime import date

# Create your models here.


send_status = (
    ('kalazio', 'ارسال توسط کالازیو'),
    ('seller', 'ارسال توسط فروشنده')
)

pay_way = (
    ('installment', 'قسطی'),
    ('together', 'یکجا')
)

send_way_order = (
    ('1', 'پست'),  # post
    ('2', 'پیک کالازیو'),  # peyk
    ('3', 'الو پیک'),  # alopeyk
)

pay_way_order = (
    ('wallet', 'کیف پول'),
    ('internet', 'پرداخت اینترنتی'),
    ('gift', 'کارت هدیه')
)

change_status = (
    ('delay', 'تحویل گرفه شده و پس از 7 روز مرجوع شده'),
    ('fast', 'پرداخت شده و پس از وارد شده به مرحله پردازش مرجوع می شود')
)

orderStatus = (
    ('1', '1'),  # در حال تکمیل سبد خرید
    ('2', '2'),  # منتظر تایید فروشنده
    ('3', '3'),  # در انتظار پرداخت
    ('4', '4'),  # پرداخت شده
    ('5', '5'),  # ارسال شده
    ('6', '6'),  # پرداخت ناموفق
    ('7', '7'),  # لغو شده
    ('8', '8'),  # مرجوعی
    ('9', '9'),  # رد شده توسط فروشنده
    ('10', '10'),  # تایید شده توسط فروشنده و در انتظار پرداخت
    ('11', '11'),  # تحویل شده
)


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name='سفارش', related_name='orderOrderitem')
    productfield = models.ForeignKey(ProductFieldFeaturesValue, on_delete=models.CASCADE, verbose_name='محصول')
    warranty = models.ForeignKey(Warranty, on_delete=models.SET_NULL, verbose_name='گارانتی', blank=True, null=True)
    seller = models.ForeignKey(Seller, verbose_name='فروشنده', on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=1, null=True, blank=True, verbose_name='تعداد')

    def __str__(self):
        if self.order.user:
            return self.order.user.username

    def get_user(self):
        return self.order.user

    get_user.short_description = 'کاربر'

    def get_order(self):
        return self.order

    get_order.short_description = 'سفارش'

    class Meta:
        verbose_name = 'جزییات محصول سبد خرید'
        verbose_name_plural = 'جزییات محصول های سبد خرید'

    def inventory(self):
        return self.product.inventory


class NextOrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    productfield = models.ForeignKey(ProductField, models.CASCADE, verbose_name='محصول')

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'جزییات سبد آینده'
        verbose_name_plural = 'جزییات سبدهای آینده'


sendTime = (
    ('1', '9-12'),
    ('2', '12-15'),
    ('3', '15-18'),
    ('4', '18-21'),
)


class Send(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name='سفارش')
    sendDate = jmodels.jDateField(verbose_name='روز ارسال(تعیین شده توسط خریدار)', blank=True, null=True)
    sendTime = models.CharField(max_length=500, verbose_name='بازه زمانی ارسال(تعیین شده توسط خریدار)',
                                choices=sendTime, blank=True,
                                null=True)

    def __str__(self):
        return self.order.user.username

    class Meta:
        verbose_name = 'زمان ارسال سفارش'
        verbose_name_plural = 'زمان ارسال سفارشات'


class Order(models.Model):
    uuid = models.CharField(max_length=300, blank=True, null=True)
    order_id = models.CharField(max_length=20, blank=True, null=True, verbose_name='مشخصه سفارش')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    orderStatus = models.CharField(max_length=100, default='1', choices=orderStatus,
                                   verbose_name='وضعیت پرداخت')
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE, blank=True, null=True, related_name='userGift')
    rate = models.IntegerField(verbose_name='امتیاز', default=0)
    sendPrice = models.FloatField(default=0.0, verbose_name='هزینه ارسال')
    created = jmodels.jDateTimeField(verbose_name='تاریخ پرداخت سفارش', null=True, blank=True, auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش ها'

    # Get order status display
    def get_orderStatus(self):
        return self.get_orderStatus_display()

    # Get total price with discount and taxation
    def get_total_price(self):
        sum = 0
        for obj in self.orderOrderitem.all():
            sum += obj.productfield.get_price_after_discount_and_taxation() * obj.quantity
        return sum

    get_total_price.short_description = 'مبلغ کلی سفارش'

    # Get order price with taxation (without discount)
    def get_total_price_without_discount(self):
        sum = 0
        for obj in self.orderOrderitem.all():
            sum += obj.productfield.get_price() * obj.quantity
        return sum

    def get_total_price_with_discount(self):
        sum = 0
        for obj in self.orderOrderitem.all():
            if obj.productfield.field.discountPersent:
                sum += (obj.productfield.get_price() - (
                    ((obj.productfield.get_price() * obj.productfield.field.discountPersent) / 100))) * obj.quantity
            else:
                sum += obj.productfield.get_price() * obj.quantity
        return sum


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='add')
    state = models.ForeignKey('State', verbose_name='استان', on_delete=models.CASCADE)
    city = models.ForeignKey('City', verbose_name='شهر', on_delete=models.CASCADE)
    postalCode = models.CharField(max_length=11, verbose_name='کد پستی')
    details = models.TextField(verbose_name='جزییات آدرس پستی')
    nighbourhood = models.CharField(max_length=500, verbose_name='محله', default='', blank=True, null=True)
    plaque = models.IntegerField(verbose_name='پلاک')
    floor = models.IntegerField(verbose_name='واحد', blank=True, null=True)
    longitude = models.CharField(max_length=1000, default='', verbose_name='طول جغرافیایی', blank=True, null=True)
    latitude = models.CharField(max_length=1000, default='', verbose_name='عرض جغرافیایی', blank=True, null=True)
    forMe = models.BooleanField(default=True, verbose_name='خودم دریافت میکنم')
    firstname = models.CharField(max_length=200, blank=True, null=True, verbose_name='نام')
    lastname = models.CharField(max_length=200, blank=True, null=True, verbose_name='نام خانوادگی')
    phone = models.CharField(max_length=11, verbose_name='تلفن', blank=True, null=True)

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'آدرس'
        verbose_name_plural = 'آدرس ها'


class State(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام استان')
    stateId = models.IntegerField(verbose_name='کد استان', blank=True, null=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان ها'

    # Get cities of a state
    def get_cities(self):
        return self.city_set_all()


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, verbose_name='استان')
    name = models.CharField(max_length=100, verbose_name='نام شهر')
    cityId = models.IntegerField(verbose_name='کد شهر', blank=True, null=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهر ها'


class Finally(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='سفارش', related_name='orderFinally')
    total_price = models.IntegerField(default=0, verbose_name='مبلغ کلی سفارش')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, verbose_name='ادرس')
    date = jmodels.jDateTimeField(verbose_name='تاریخ پرداخت سفارش', null=True, blank=True)
    time = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='تاریخ ثبت سفارش')
    pay_date = jmodels.jDateField(verbose_name='تاریخ پرداخت', blank=True, null=True)
    ticket = models.TextField(verbose_name='تیکت', blank=True, null=True)
    description = models.TextField(verbose_name='توضیحات', blank=True, null=True)
    SystemTraceNo = models.CharField(max_length=20, verbose_name='شماره مرجع', blank=True, null=True)
    RetrivalRefNo = models.CharField(max_length=20, verbose_name='شماره پیگیری تراکنش', blank=True, null=True)
    PostTracking = models.CharField(max_length=20, verbose_name='شماره پیگیری پست', blank=True, null=True)
    PostBarcode = models.CharField(max_length=20, verbose_name='شماره بارکد پست', blank=True, null=True)
    sendStatus = models.CharField(max_length=30, choices=send_status, default='kalazio', verbose_name='ارسال')
    sendWayOrder = models.CharField(max_length=30, choices=send_way_order, blank=True, null=True, default='',
                                    verbose_name='گزینه ارسال')
    payWayOrder = models.CharField(max_length=30, choices=pay_way_order, default='internet',
                                   verbose_name='روش پرداخت سفارش')
    changeStatus = models.CharField(max_length=30, choices=change_status, verbose_name='تغییر وضعیت سفارش', default='',
                                    blank=True, null=True)
    confirm = models.CharField(max_length=256,
                               choices=[('1', 'نیاز به تایید فروشنده دارد'), ('2', 'نیاز به تایید فروشنده ندارد')],
                               verbose_name='تایید توسط فروشنده', default='2')
    sellerConfirmTime = models.DateTimeField(blank=True, null=True, verbose_name='زمان ارسال (توسط فروشنده)')
    previous_state = False
    payWay = models.CharField(max_length=30, choices=pay_way, default='together', verbose_name='نحوه پرداخت')
    pay = models.CharField(max_length=256, choices=[('1', 'پرداخت شده'), ('2', 'پرداخت نشده')],
                           verbose_name='پرداخت شده یا پرداخت نشده', default='2')
    pay_link = models.CharField(max_length=300, verbose_name='لینک پرداخت', blank=True, null=True)

    def __str__(self):
        return str(self.order.id)

    class Meta:
        verbose_name = 'سفارش ثبت شده'
        verbose_name_plural = 'سفارشات ثبت شده'

    def get_price(self):
        return self.order.get_total_price() + self.order.sendPrice

    # def save(self, *args, **kwargs):
    #     self.total_price = self.order.get_total_price() + self.order.sendPrice
    #     super(Finally, self).save(*args, **kwargs)

    get_price.short_description = 'قیمت (با تخفیف)'

    # Get change status of order display
    def get_changeStatus(self):
        return self.get_changeStatus_display()

    # Get pay way order display
    def get_payWayOrder(self):
        return self.get_payWayOrder_display()

    # Get send way order display
    def get_sendWayOrder(self):
        return self.get_sendWayOrder_display()

    # Get pay way display
    def get_payWay(self):
        return self.get_payWay_display()

    # Get send status display
    def get_sendStatus(self):
        return self.get_payWay_sendStatus()

    def get_confirm(self):
        return self.get_confirm_display()

    get_confirm.short_description = 'تایید توسط فروشنده'

    def get_pay(self):
        return self.get_pay_display()

    get_pay.short_description = 'پرداخت شده یا پرداخت نشده'

    def get_order_id(self):
        return self.order.order_id

    get_order_id.short_description = 'مشخصه سفارش'

    def get_sendDay(self):
        send = Send.objects.get(order=self.order)
        return str(send.sendDate)

    get_sendDay.short_description = 'روز ارسال سفارش (تعیین شده توسط خریدار)'

    def get_sendTime(self):
        send = Send.objects.get(order=self.order)
        return str(send.get_sendTime_display())

    get_sendTime.short_description = 'بازه زمانی ارسال سفارش (تعیین شده توسط خریدار)'


cancel_status = (
    ('referred', 'مرجوع شده'),
    ('returning', 'در حال مرجوعی')
)


class CancelOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='سغارش', blank=True, null=True)
    paymentNumber = models.CharField(max_length=20, verbose_name='شماره پیگیری پرداخت')
    status = models.CharField(max_length=20, choices=cancel_status, verbose_name='وضعیت مرجوعی', default='')
    referred_date = jmodels.jDateField(verbose_name='تاریخ مرجوعی', blank=True, null=True)
    accountNumber = models.IntegerField(verbose_name='شماره حساب')

    def __str__(self):
        return str(self.order.id)

    class Meta:
        verbose_name = 'سفارش مرجوعی'
        verbose_name_plural = 'سفارشات مرجوعی'
