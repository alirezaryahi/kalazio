import math
from django.conf import settings
from django.db import models

# Create your models here.
from django.dispatch import receiver


class BrandRepresentative(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="کاربر",
        blank=True,
        null=True,
    )
    position = models.CharField(max_length=100, verbose_name="سمت و جایگاه")
    companyEmail = models.EmailField(verbose_name="ایمیل شرکت")
    active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.user.username if self.user else str(self.id)

    class Meta:
        verbose_name = "نماینده برند"
        verbose_name_plural = "نماینده های برندها"


class SellerRepresentative(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="کاربر",
        blank=True,
        null=True,
    )
    position = models.CharField(max_length=100, verbose_name="سمت و جایگاه")
    active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.user.username if self.user else str(self.id)

    class Meta:
        verbose_name = "نماینده فروشنده"
        verbose_name_plural = "نماینده های فروشنده ها"


typee = (
    ("partner", "حساب سهیم"),
    ("kalazio", "حساب کالازیو"),
    ("original", "حساب اصلی فروشنده"),
)


class Partner(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام سهیم")
    ibanNumber = models.CharField(max_length=100, verbose_name="شماره شبا")
    accountNumber = models.CharField(
        max_length=100, verbose_name="شماره حساب", blank=True, null=True
    )
    percent = models.IntegerField(default=0, verbose_name="درصد")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "سهیم"
        verbose_name_plural = "سهیم ها"
