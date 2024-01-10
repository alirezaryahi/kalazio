from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Category,
    SpicialField,
    SpicialFieldValue,
    GalleryVideo,
    GalleryImage,
    Product,
    FavoriteProduct,
    Seller,
    Visited,
    RateProduct,
    Warranty,
    ProductField,
    Evidence,
    UserEvidence,
    ProductSpicialField,
    CategorySpicialField, ProductFieldFeaturesValue, ProductFieldFeaturesKey
)
from django.utils.html import format_html, format_html_join


# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'advocate', 'get_spicialfield', 'add_spicialfield')
    list_filter = ('parent', 'advocate')
    search_fields = ('title',)

    class Meta:
        model = Category

    def get_spicialfield(self, obj):
        cell_contents = []
        for i in obj.categoryspicial.all():
            cell_contents.append(
                format_html(
                    '<a  href="{0}{1}/change/">{2}</a>, ',
                    reverse('admin:product_categoryspicialfield_changelist'), i.id,
                    {i.spicialField.spicialField.key: i.spicialField.value})
            )
        return mark_safe('\n'.join(cell_contents))

    get_spicialfield.short_description = 'مشخصات ویژه'
    get_spicialfield.allow_tags = True

    def add_spicialfield(self, obj):
        return format_html(
            '<a  href="{0}" class="button">اضافه کردن</a>',
            reverse('admin:product_categoryspicialfield_add'))

    add_spicialfield.short_description = 'اضافه کردن مشخصات ویژه'
    get_spicialfield.allow_tags = True

    class Media:
        js = ('js/admin/CategoryAdmin.js',)


admin.site.register(Category, CategoryAdmin)


class ProductSpicialFieldAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'product')
    search_fields = ('product__name',)

    class Meta:
        model = ProductSpicialField


admin.site.register(ProductSpicialField, ProductSpicialFieldAdmin)


class CategorySpicialFieldAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'category')
    search_fields = ('category__title',)

    class Meta:
        model = CategorySpicialField


admin.site.register(CategorySpicialField, CategorySpicialFieldAdmin)
admin.site.register(Evidence)


class UserEvidenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'evidence', 'evidenceConfirm', 'get_userevidence', 'add_userevidence')
    list_filter = ('evidenceConfirm',)
    search_fields = ('user',)

    class Meta:
        model = UserEvidence

    def get_userevidence(self, obj):
        cell_contents = []
        for i in UserEvidence.objects.filter(user=obj.user):
            cell_contents.append(
                format_html(
                    '<a  href="{0}{1}/change/">{2}</a>, ',
                    reverse('admin:product_userevidence_changelist'), i.id,
                    i.evidence.title)
            )
        return mark_safe('\n'.join(cell_contents))

    get_userevidence.short_description = 'مدارک ارسالی کاربر'
    get_userevidence.allow_tags = True

    def add_userevidence(self, obj):
        return format_html(
            '<a  href="{0}" class="button">اضافه کردن</a>',
            reverse('admin:product_userevidence_add'))

    add_userevidence.short_description = 'اضافه کردن مدرک کاربر'
    add_userevidence.allow_tags = True


admin.site.register(UserEvidence, UserEvidenceAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'tag_list', 'like_number', 'visit', 'get_spicialfield', 'add_spicialfield')
    list_filter = ('category',)
    search_fields = ('name', 'tags__name')
    exclude = ('visit', 'like_number')

    class Meta:
        model = Product

    def get_spicialfield(self, obj):
        cell_contents = []
        for i in obj.productspicial.all():
            cell_contents.append(
                format_html(
                    '<a  href="{0}{1}/change/">{2}</a>, ',
                    reverse('admin:product_productspicialfield_changelist'), i.id,
                    {i.spicialField.spicialField.key: i.spicialField.value})
            )
        return mark_safe('\n'.join(cell_contents))

    get_spicialfield.short_description = 'مشخصات ویژه'
    get_spicialfield.allow_tags = True

    def add_spicialfield(self, obj):
        return format_html(
            '<a  href="{0}" class="button">اضافه کردن</a>',
            reverse('admin:product_productspicialfield_add'))

    add_spicialfield.short_description = 'اضافه کردن مشخصات ویژه'
    get_spicialfield.allow_tags = True

    class Media:
        js = ('js/admin/ProductAdmin.js',)


admin.site.register(Product, ProductAdmin)


class ProductFieldAdmin(admin.ModelAdmin):
    list_display = (
        'product', 'seller', 'sell_number', 'comment_number', 'advocate_number', 'specialoffer')
    list_filter = ('specialoffer',)
    search_fields = ('product_name',)
    exclude = ('advocate_number', 'comment_number', 'buy_users')

    class Meta:
        model = ProductField

    class Media:
        js = ('js/admin/ProductAdmin.js',)


admin.site.register(ProductField, ProductFieldAdmin)


class ProductFieldFeaturesValueAdmin(admin.ModelAdmin):
    list_display = ('field', 'inventory', 'get_price_after_discount_and_taxation', 'get_price_after_discount')

    class Meta:
        model = ProductFieldFeaturesValue

    class Media:
        js = ('js/admin/ProductAdmin.js',)


admin.site.register(ProductFieldFeaturesValue, ProductFieldFeaturesValueAdmin)


class FavoriteProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')
    search_fields = ('user',)

    class Meta:
        model = FavoriteProduct

    class Media:
        js = ('js/admin/FavoriteProductAdmin.js',)


admin.site.register(FavoriteProduct, FavoriteProductAdmin)


class VisitProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')
    search_fields = ('user',)

    class Meta:
        model = Visited

    class Media:
        js = ('js/admin/FavoriteProductAdmin.js',)


admin.site.register(Visited, VisitProductAdmin)
admin.site.register(GalleryVideo)
admin.site.register(ProductFieldFeaturesKey)


class GalleryImageAdmin(admin.ModelAdmin):

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" height=100 width=100 />'.format(settings.SITE_URI + obj.image.url))
        return None

    list_display = ['image_tag', ]


admin.site.register(GalleryImage, GalleryImageAdmin)
admin.site.register(SpicialField)


class SpicialFieldValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'spicialField')

    class Meta:
        model = SpicialFieldValue


admin.site.register(SpicialFieldValue, SpicialFieldValueAdmin)


class RateProductAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'product')
    search_fields = ('product',)

    class Meta:
        model = RateProduct


admin.site.register(RateProduct, RateProductAdmin)


class WarrantyAdmin(admin.ModelAdmin):
    list_display = ('name', 'month')
    search_fields = ('name',)

    class Meta:
        model = Warranty


admin.site.register(Warranty, WarrantyAdmin)


# admin.site.register(ApplyingForProduct)


class SellerAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'feature', 'mobile')
    search_fields = ('title',)
    list_filter = ('brand',)

    class Meta:
        model = Seller


admin.site.register(Seller, SellerAdmin)
