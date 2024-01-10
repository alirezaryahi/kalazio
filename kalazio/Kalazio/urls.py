"""Kalazio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import order
from .views import (
    Search,
    MainMoreComment,
    MainMoreLike,
    MainRandomMoreLike,
    MainMoreVisit,
    MainSpecialOfferAndMediaBrandAndDiscountPriceAndRandomBrand,
    MainMomentaryProduct,
    MainAdvocateCategory,
    MainLatestAndMoreSellProduct,
    MainVisitedProductOfUser,
    RandomBrandBanner, MainRelatedVisitedProductOfUser, SearchData
)

urlpatterns = [
    path('search/', Search.as_view()),
    path('search-data/', SearchData.as_view()),

    # main page api
    path('main-more-comment/', MainMoreComment.as_view()),
    path('main-more-like/', MainMoreLike.as_view()),
    path('main-random-more-like/', MainRandomMoreLike.as_view()),
    path('main-more-visit/', MainMoreVisit.as_view()),
    path('main-specialoffer-mediabrand-discountprice-randombrand/',
         MainSpecialOfferAndMediaBrandAndDiscountPriceAndRandomBrand.as_view()),
    path('main-momentary-product/', MainMomentaryProduct.as_view()),
    path('main-advocate-category/', MainAdvocateCategory.as_view()),
    path('main-latest-moresell-product/', MainLatestAndMoreSellProduct.as_view()),
    path('main-visited-product-user/', MainVisitedProductOfUser.as_view()),
    path('main-related-visited-product-user/', MainRelatedVisitedProductOfUser.as_view()),
    path('random-brand-banner/', RandomBrandBanner.as_view()),

    # --------------------------------------------------------------------------------------------
    path('admin/', admin.site.urls),
    path('products/', include('product.urls')),
    path('brands/', include('brand.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('order/', include('order.urls')),
    path('adminPanel/', include('adminPanel.urls')),
    path('user/', include('user.urls')),
    path('comment/', include('comments.urls')),
    path('questionAndAnswer/', include('questionAndAnswer.urls')),
    path('contactus/', include('contactus.urls')),
]
