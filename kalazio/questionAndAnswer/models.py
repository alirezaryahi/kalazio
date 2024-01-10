from django.db import models
from django_jalali.db import models as jmodels


# Create your models here.


class QuestionAndAnswer(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="کاربر",
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        verbose_name="پاسخ",
    )
    title = models.CharField(
        max_length=300, verbose_name="عنوان", blank=True, null=True
    )
    product = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE, verbose_name="محصول"
    )
    content = models.TextField(verbose_name="متن پیام")
    date = jmodels.jDateField(
        verbose_name="تاریخ کامنت",
        help_text="تاریخ را به این شکل وارد کنید : 01-01-1400",
        auto_now_add=True,
    )
    likeNumber = models.ManyToManyField(
        "LikeQuestionAndAnswer",
        blank=True,
        verbose_name="لایک",
        related_name="questionLike",
    )
    editNumber = models.IntegerField(default=0, verbose_name="تعداد ویرایش فروشنده")
    confirm = models.BooleanField(default=False, verbose_name="تایید")

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "پرسش و پاسخ"
        verbose_name_plural = "لیست پرسش و پاسخ"

    # Get child of parent question and answer
    def get_child(self):
        list = []
        query = self.questionandanswer_set.all()
        for q in query:
            list.append(q)
        list2 = []
        for li in list:
            list2.append(
                {
                    "name": li["user"],
                    "title": li["title"],
                    "content": li["content"],
                    "date": str(li["date"]),
                }
            )
        return list2


class LikeQuestionAndAnswer(models.Model):
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        verbose_name="کاربر",
        related_name="likeQuestionAndAnswerUser",
    )
    questionAndAnswer = models.ForeignKey(
        QuestionAndAnswer, on_delete=models.CASCADE, verbose_name="نظر"
    )

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = "پرسش و پاسخ مورد علاقه"
        verbose_name_plural = "پرسش و پاسخ های مورد علاقه"
