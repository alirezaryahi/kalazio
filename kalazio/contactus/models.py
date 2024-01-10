from django.db import models


# Create your models here.


class ContactUs(models.Model):
    fullname = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی")
    email = models.EmailField(verbose_name="ایمیل")
    title = models.CharField(max_length=200, verbose_name="عنوان پیام")
    content = models.TextField(verbose_name="متن پیام")

    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام ها"
