from django.contrib import admin
from .models import Address, Order, OrderItem, State, City, Finally, CancelOrder, NextOrderItem, Send


# Register your models here.


class FinallyAdmin(admin.ModelAdmin):
    def price(self, obj):
        return obj.get_price()

    def order_status(self, obj):
        status = ''
        if obj.order.orderStatus == '1':
            status = 'در حال تکمیل سبد خرید'
        if obj.order.orderStatus == '2':
            status = 'منتظر تایید فروشنده'
        if obj.order.orderStatus == '3':
            status = 'در انتظار پرداخت'
        if obj.order.orderStatus == '4':
            status = 'پرداخت شده'
        if obj.order.orderStatus == '5':
            status = 'ارسال شده'
        if obj.order.orderStatus == '6':
            status = 'پرداخت ناموفق'
        if obj.order.orderStatus == '7':
            status = 'لغو شده'
        if obj.order.orderStatus == '8':
            status = 'مرجوعی'
        if obj.order.orderStatus == '9':
            status = 'رد شده توسط فروشنده'
        if obj.order.orderStatus == '10':
            status = 'تایید شده توسط فروشنده و در انتظار پرداخت'
        if obj.order.orderStatus == '11':
            status = 'تحویل شده'
        return status

    order_status.short_description = 'وضعیت سفارش'

    fields = ('order', 'user', 'get_price', 'address', 'ticket', 'date', 'description', 'SystemTraceNo',
              'RetrivalRefNo', 'PostTracking', 'PostBarcode', 'sendStatus', 'sendWayOrder',
              'payWayOrder', 'changeStatus', 'get_confirm', 'get_pay', 'pay_link', 'get_sendDay', 'get_sendTime',
              'order_status', 'get_order_id')
    readonly_fields = (
        'get_sendDay', 'get_sendTime', 'get_price', 'get_confirm', 'get_pay', 'get_sendDay', 'get_sendTime',
        'order_status', 'get_order_id')
    list_display = (
        'order', 'user', 'get_confirm', 'get_price', 'pay_date', 'sendWayOrder', 'payWayOrder', 'get_pay',
        'get_sendDay', 'get_sendTime', 'sellerConfirmTime')

    search_fields = ('user__username', 'order__id')

    class Meta:
        model = Finally


admin.site.register(Finally, FinallyAdmin)


class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'forMe', 'postalCode')
    search_fields = ('user__username',)

    class Meta:
        model = Address


admin.site.register(Address, AddressAdmin)


class SendAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'sendDate', 'sendTime')

    class Meta:
        model = Send


admin.site.register(Send, SendAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'orderStatus', 'get_total_price', 'sendPrice', 'uuid')
    search_fields = ('user__username',)
    list_filter = ('orderStatus',)

    class Meta:
        model = Order

    def get_id(self, obj):
        return obj.id


admin.site.register(Order, OrderAdmin)


class CancelOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'paymentNumber', 'referred_date', 'accountNumber')
    search_fields = ('order',)

    class Meta:
        model = CancelOrder


admin.site.register(CancelOrder, CancelOrderAdmin)


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('get_order', 'get_user', 'productfield', 'seller', 'quantity')
    search_fields = ('order__id',)

    class Meta:
        model = OrderItem


admin.site.register(OrderItem, OrderItemAdmin)


class NextOrderItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'productfield')
    search_fields = ('user',)

    class Meta:
        model = NextOrderItem


admin.site.register(NextOrderItem, NextOrderItemAdmin)

admin.site.register(State)
admin.site.register(City)
