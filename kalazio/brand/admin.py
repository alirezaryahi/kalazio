from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import ImageBanner, VideoBanner, Brand, RateBrand, Banner


# Register your models here.
class ImageBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'link')
    search_fields = ('title',)

    class Meta:
        model = ImageBanner


admin.site.register(ImageBanner, ImageBannerAdmin)

admin.site.register(VideoBanner)
admin.site.register(RateBrand)
admin.site.register(Banner)


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialoffer', 'tick', 'get_imageBanner', 'add_imageBanner', 'get_videoBanner',
                    'add_videoBanner')
    list_filter = ('tick',)
    search_fields = ('name',)

    class Meta:
        model = Brand

    def get_imageBanner(self, obj):
        cell_contents = []
        for i in ImageBanner.objects.filter(brand=obj):
            cell_contents.append(
                format_html(
                    '<a  href="{0}{1}/change/">{2}</a>, ',
                    reverse('admin:brand_imagebanner_changelist'), i.id,
                    i.title)
            )
        return mark_safe('\n'.join(cell_contents))

    get_imageBanner.short_description = 'بنر تصویری'
    get_imageBanner.allow_tags = True

    def add_imageBanner(self, obj):
        return format_html(
            '<a  href="{0}" class="button">اضافه کردن</a>',
            reverse('admin:brand_imagebanner_add'))

    add_imageBanner.short_description = 'اضافه کردن بنر تصویری'
    add_imageBanner.allow_tags = True

    def get_videoBanner(self, obj):
        cell_contents = []
        for i in VideoBanner.objects.filter(brand=obj):
            cell_contents.append(
                format_html(
                    '<a  href="{0}{1}/change/">{2}</a>, ',
                    reverse('admin:brand_videobanner_changelist'), i.id,
                    i.title)
            )
        return mark_safe('\n'.join(cell_contents))

    get_videoBanner.short_description = 'بنر ویدیویی'
    get_videoBanner.allow_tags = True

    def add_videoBanner(self, obj):
        return format_html(
            '<a  href="{0}" class="button">اضافه کردن</a>',
            reverse('admin:brand_videobanner_add'))

    add_videoBanner.short_description = 'اضافه کردن بنر ویدیویی'
    add_videoBanner.allow_tags = True

    class Media:
        js = ('js/admin/BrandAdmin.js',)


admin.site.register(Brand, BrandAdmin)
