from django.db import models
from django_jalali.db import models as jmodels
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

# Create your models here.

number_rate = (
    ('5', 'عالی'),
    ('4', 'خوب'),
    ('3', 'معمولی'),
    ('2', 'بد'),
    ('1', 'خیلی بد'),
)

rate = (
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
)

suggest = (
    ('suggest', 'پیشنهاد می کنم'),
    ('dont suggest', 'پیشنهاد نمی کنم'),
    ('no idea', 'نظری ندارم')
)

status = (
    ('user', 'کاربر'),
    ('buyer', 'خریدار'),
)


class Rate(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر')
    spicialField = models.ForeignKey('product.ProductSpicialField', on_delete=models.CASCADE, verbose_name='ویژگی', blank=True,
                                     null=True, related_name='spicial')
    number = models.CharField(max_length=10, choices=number_rate, verbose_name='امتیاز')

    def __str__(self):
        return str(self.id)

    def product(self):
        return self.spicialField.product

    product.short_description = 'محصول'

    class Meta:
        verbose_name = 'امتیاز'
        verbose_name_plural = 'امتیاز ها'


class Comment(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر')
    status = models.CharField(max_length=20, choices=status, verbose_name='وضعیت کاربر', blank=True, null=True,
                              default='user')
    product_field_id = models.ForeignKey('product.ProductField', on_delete=models.CASCADE, verbose_name='محصول')
    detailRate = models.ManyToManyField(Rate, blank=True, verbose_name='امتیاز جزیی', default='')
    show = models.BooleanField(default=False, verbose_name='عدم نمایش مشخصات')
    title = models.CharField(max_length=200, verbose_name='عنوان پیام')
    content = models.TextField(verbose_name='متن پیام')
    suggest = models.CharField(max_length=30, choices=suggest, verbose_name='پیشنهاد خرید')
    point = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='امتیاز (1 تا 5)')
    date = jmodels.jDateField(verbose_name='تاریخ کامنت', help_text="تاریخ را به این شکل وارد کنید : 01-01-1400",
                              auto_now_add=True)
    confirm = models.BooleanField(default=False, verbose_name='تایید')

    def __str__(self):
        return str(self.user)

    # Get suggest display
    def get_suggest(self):
        return self.get_suggest_display()

    # Get status display
    def get_status(self):
        return self.get_status_display()

    class Meta:
        verbose_name = 'کامنت'
        verbose_name_plural = 'کامنت ها'

    # Get child of each comment
    def get_child(self):
        list = []
        query = self.comment_set.all()
        for q in query:
            list.append(q)
        list2 = []
        for li in list:
            list2.append({'name': li['user'], 'title': li['title'], 'content': li['content'], 'date': str(li['date'])})
        return list2


class LikeComment(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر',
                             related_name='likeCommentUser')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'نظر مورد علاقه'
        verbose_name_plural = 'نظرات مورد علاقه'


class DisLikeComment(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='کاربر',
                             related_name='dislikeCommentUser')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = 'نظر غیر مورد علاقه'
        verbose_name_plural = 'نظرات غیر مورد علاقه'


class GoodPoint(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')
    good_text = models.TextField(verbose_name='نقطه قوت')

    def __str__(self):
        return self.comment.product_field_id.product.name

    class Meta:
        verbose_name = 'نقطه قوت'
        verbose_name_plural = 'نقاط قوت'


class WeakPoint(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')
    weak_text = models.TextField(verbose_name='نقطه ضعف')

    def __str__(self):
        return self.comment.product_field_id.product.name

    class Meta:
        verbose_name = 'نقطه ضعف'
        verbose_name_plural = 'نقاط ضعف'


class ImageComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')
    image = models.ImageField(upload_to='comment_image/', verbose_name='تصویر', blank=True, null=True)

    def __str__(self):
        return self.comment.product_field_id.product.name

    # Get url of image field
    def get_absolute_url(self):
        if self.image:
            return settings.SITE_URI + '{path}'.format(path=self.image.url)
        return ''

    class Meta:
        verbose_name = 'تصویر نظر'
        verbose_name_plural = 'تصاویر نظر'


class VideoComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='نظر')
    video = models.FileField(upload_to='comment_video/', verbose_name='فیلم', blank=True, null=True)

    def __str__(self):
        return self.comment.product_field_id.product.name

    # # Get url of video field
    def get_absolute_url(self):
        if self.video:
            return settings.SITE_URI + '{path}'.format(path=self.video.url)
        return ''

    class Meta:
        verbose_name = 'فیلم نظر'
        verbose_name_plural = 'فیلم های نظر'
