from django.contrib import admin
from .models import BrandRepresentative, SellerRepresentative, Partner


# Register your models here.


class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "ibanNumber",
        "accountNumber",
        "percent",
    )

    class Meta:
        model = Partner


admin.site.register(Partner, PartnerAdmin)


class BrandRepresentativeAdmin(admin.ModelAdmin):
    list_display = ("__str__",)

    class Meta:
        model = BrandRepresentative


admin.site.register(BrandRepresentative, BrandRepresentativeAdmin)


class SellerRepresentativeAdmin(admin.ModelAdmin):
    list_display = ("__str__",)

    class Meta:
        model = SellerRepresentative


admin.site.register(SellerRepresentative, SellerRepresentativeAdmin)
