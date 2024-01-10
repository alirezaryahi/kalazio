from django.urls import path
from .views import (
    DetailOfBrand,
    ExpensiveProductOfBrand,
    InExpensiveProductOfBrand,
    LatestProductOfBrand,
    MoreLikeProductOfBrand,
    MoreVisitProductOfBrand,
    MoreSellNumberProductOfBrand,
    AllBrand,
    AllBanner,
)

urlpatterns = [
    path('all-banner/', AllBanner.as_view()),
    path('<int:pk>/', DetailOfBrand.as_view()),
    path('all-brand/', AllBrand.as_view()),
    path('inexpensive-product-brand/<int:pk>/', InExpensiveProductOfBrand.as_view()),
    path('expensive-product-brand/<int:pk>/', ExpensiveProductOfBrand.as_view()),
    path('latest-product-brand/<int:pk>/', LatestProductOfBrand.as_view()),
    path('liked-product-brand/<int:pk>/', MoreLikeProductOfBrand.as_view()),
    path('visited-product-brand/<int:pk>/', MoreVisitProductOfBrand.as_view()),
    path('bestsellers-product-brand/<int:pk>/', MoreSellNumberProductOfBrand.as_view()),
]
