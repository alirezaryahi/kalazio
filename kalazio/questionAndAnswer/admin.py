from django.contrib import admin
from .models import QuestionAndAnswer, LikeQuestionAndAnswer


# Register your models here.


class QuestionAndAnswerAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "parent", "editNumber")
    search_fields = ("product", "user")
    list_filter = ("confirm",)
    exclude = ("editNumber",)

    class Meta:
        model = QuestionAndAnswer

    class Media:
        js = ("js/admin/GalleryVideoAdmin.js",)


admin.site.register(QuestionAndAnswer, QuestionAndAnswerAdmin)
admin.site.register(LikeQuestionAndAnswer)
