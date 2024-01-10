from django.contrib import admin
from .models import Report


# Register your models here.


class ReportAdmin(admin.ModelAdmin):
    list_display = ("user", "questionAndAnswer", "comments", "date")
    search_fields = ("user",)

    class Meta:
        model = Report


admin.site.register(Report, ReportAdmin)
