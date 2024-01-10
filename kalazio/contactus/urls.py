from django.urls import path
from .views import ContactUsCreate

urlpatterns = [path("create/", ContactUsCreate.as_view())]
