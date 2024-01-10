from django.contrib import admin
from .models import User, Gift, Notifications, PhoneAuthenticated, Samava


# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_active', 'email', 'codeMelli', 'authorized', 'role')
    list_filter = ('is_active',)
    search_fields = ('last_name',)
    exclude = ('password', 'register_number', 'register_date')

    class Meta:
        model = User

    class Media:
        js = ('js/admin/ProfileAdmin.js',)


admin.site.register(User, ProfileAdmin)
admin.site.register(Samava)


class NotificationsAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'title', 'get_level',)
    list_filter = ('level',)
    search_fields = ('user__username',)

    class Meta:
        model = Notifications

    def get_user(self, obj):
        return str(obj.user)

    get_user.short_description = 'کاربر'


admin.site.register(Notifications, NotificationsAdmin)


class GiftAdmin(admin.ModelAdmin):
    list_display = ('serial', 'amount', 'orderCode', 'donator', 'user', 'use')
    list_filter = ('use',)
    search_fields = ('serial', 'orderCode', 'donator', 'user')

    class Meta:
        model = Gift

    class Media:
        js = ('js/admin/GiftAdmin.js',)


admin.site.register(Gift, GiftAdmin)

admin.site.register(PhoneAuthenticated)
