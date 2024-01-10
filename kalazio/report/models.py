from django.db import models
from questionAndAnswer.models import QuestionAndAnswer
from comments.models import Comment
from product.models import Product
from user.models import User
from django_jalali.db import models as jmodels


# Create your models here.


class Report(models.Model):
    questionAndAnswer = models.ForeignKey(
        QuestionAndAnswer,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="پرسش و پاسخ",
    )
    comments = models.ForeignKey(
        Comment, on_delete=models.CASCADE, blank=True, null=True, verbose_name="نظرات"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="کاربر", related_name="userReport"
    )
    content = models.TextField(verbose_name="متن ریپورت")
    date = jmodels.jDateField(
        verbose_name="تاریخ کامنت",
        help_text="تاریخ را به این شکل وارد کنید : 01-01-1400",
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = "ریپورت"
        verbose_name_plural = "ریپورت ها"
