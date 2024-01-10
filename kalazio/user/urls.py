from django.urls import path
from .views import (
    NotificationList,
    FavoriteOfUserList,
    FavoriteOfUserCreate,
    FavoriteOfUserDelete,
    QuestionAndAnswerOfUser,
    OrdersOfUser,
    user_login_register,
    user_login_check_code,
    UserEdit,
    UserGiftBuy,
    UserGiftReceive,
    # get_token,
    # refresh_token,
    get_samava_url,
    get_samava_token
)

urlpatterns = [
    # path('register-melli/', get_token),

    path('', UserEdit.as_view()),

    path('login-register/', user_login_register),
    path('login-code/', user_login_check_code),

    path('notifications/', NotificationList.as_view()),
    path('favorite-product-list/<int:pk>/', FavoriteOfUserList.as_view()),
    path('favorite-product-create/', FavoriteOfUserCreate.as_view()),
    path('favorite-product-delete/<int:pk>/', FavoriteOfUserDelete.as_view()),
    path('question-answer-user/<int:pk>/', QuestionAndAnswerOfUser.as_view()),
    path('orders-user/<int:pk>/', OrdersOfUser.as_view()),
    path('gift-list-buy/', UserGiftBuy.as_view()),
    path('gift-list-receive/', UserGiftReceive.as_view()),

    # samava
    path('get-samava-url/', get_samava_url),
    path('get-samava-token/', get_samava_token),
]
