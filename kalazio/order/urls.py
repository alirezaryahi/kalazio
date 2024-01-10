from django.urls import path
from .views import (
    order_item_delete,
    order_item_inc,
    order_item_dec,
    get_complete_order,
    CreateAddress,
    GetAllAddress,
    RetrieveAddress,
    order_item,
    # SetDiscount,
    # CreateFinally,
    CancelOrder,
    NextOrderItemCreate,
    NextOrderItemDelete,
    NextOrderItemList,
    # PreBuyCreate,
    # PreBuyDelete,
    # PreBuyList,
    UserRecentVisitedProduct,
    UserRecentProductBuy,
    RelatedCartProduct,
    FailOrders,
    CancelFailOrder,
    OrderView,
    Factor,
    AddGiftToOrder,
    SendDateAndSendTime,
    StateListView,
    get_city,
    SellerConfirm,
    SellerConfirmList,
    SellerConfirmMob,
    CurrentFinally,
    OrderViewDetail,
    payment_verify,
    CancelFinallyOrder,
    create_finally,
    StateCityListView,
    OrderReport,
    OrdersReport,
    PostState,
    PostCity,
    PostCityList,
    PostStateList,
    SendPrice,
    count_order,
    get_payment_url
)

urlpatterns = [
    path('state/', StateListView.as_view()),
    path('state-city/', StateCityListView.as_view()),
    path('state/<int:pk>/', get_city),
    path('', OrderView.as_view()),  #############
    path('detail/<int:id>/', OrderViewDetail.as_view()),  #############
    path('order-item/', order_item),  ###########
    path('add-gift-order/', AddGiftToOrder.as_view()),  ########
    path('factor/<int:pk>/', Factor.as_view()),  #######
    path('fail-orders/', FailOrders.as_view()),  ########
    path('cancel-fail-orders/<int:pk>/', CancelFailOrder.as_view()),  ##############
    path('cancel-finally-orders/', CancelFinallyOrder.as_view()),  ##############
    path('order-item-delete/<int:pk>/', order_item_delete),  ##############3
    path('order-item-inc/', order_item_inc),  ###########
    path('order-item-dec/', order_item_dec),  ################
    path('get-complete-order/', get_complete_order),  ############
    path('get-send-time/', SendDateAndSendTime.as_view()),  ########
    # path('create-finally/', CreateFinally.as_view()),  ######
    path('current-finally/', CurrentFinally.as_view()),  ######
    path('seller-confirm/', SellerConfirm.as_view()),  ######
    path('seller-confirm-mob/<int:finall>/<int:user>/', SellerConfirmMob.as_view()),  ######
    path('seller-confirm-list/', SellerConfirmList.as_view()),  ######
    path('user-recent-product-buy/<int:pk>/', UserRecentProductBuy.as_view()),  ####
    path('user-recent-visited-product/', UserRecentVisitedProduct.as_view()),  #####
    path('related-cart-product/<int:pk>/', RelatedCartProduct.as_view()),  ######

    # cancel order api
    path('cancel-order/', CancelOrder.as_view()),  #####

    # count order
    path('count-order/', count_order),  #####

    # next order api
    path('next-order-create/', NextOrderItemCreate.as_view()),  ######
    path('next-order-delete/<int:pk>/', NextOrderItemDelete.as_view()),  #####
    path('next-order-list/', NextOrderItemList.as_view()),  ######

    # address api
    path('get-all-address/', GetAllAddress.as_view()),  #####
    path('create-address/', CreateAddress.as_view()),
    path('retreive-address/<int:pk>/', RetrieveAddress.as_view()),

    # pay
    path('send-request/', create_finally),
    path('get-payment-url/', get_payment_url),
    path('verify/payment/', payment_verify),

    # price
    path('send-price/', SendPrice.as_view()),

    # report
    path('orders-report/', OrdersReport.as_view()),
    path('order-report/', OrderReport.as_view()),

    # post
    path('post-state-list/', PostState.as_view()),
    path('post-city-list/', PostCity.as_view()),
    path('post-city/', PostCityList.as_view()),
    path('post-state/', PostStateList.as_view()),
]
