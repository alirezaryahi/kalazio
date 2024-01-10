from django.contrib import admin
from comments.models import Comment, Rate, LikeComment, DisLikeComment, GoodPoint, WeakPoint, ImageComment, VideoComment


# Register your models here.


class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_field_id', 'date')
    search_fields = ('product_field_id', 'user')
    list_filter = ('confirm',)

    class Meta:
        model = Comment

    class Media:
        js = ('js/admin/CommentProductAdmin.js',)


admin.site.register(Comment, CommentAdmin)


class RateAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', '__str__', 'number')
    search_fields = ('product', 'user')

    class Meta:
        model = Rate


admin.site.register(Rate, RateAdmin)
admin.site.register(LikeComment)
admin.site.register(DisLikeComment)


class GoodPointAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user')

    class Meta:
        model = GoodPoint

    def user(self, obj):
        return obj.comment.user

    user.short_description = 'کاربر'


admin.site.register(GoodPoint, GoodPointAdmin)


class WeakPointAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user')

    class Meta:
        model = WeakPoint

    def user(self, obj):
        return obj.comment.user

    user.short_description = 'کاربر'


admin.site.register(WeakPoint, WeakPointAdmin)
admin.site.register(ImageComment)
admin.site.register(VideoComment)
