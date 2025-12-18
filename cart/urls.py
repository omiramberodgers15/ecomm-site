from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('json/', views.cart_json, name='cart_json'),


    # Checkout & DPO
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/dpo/', views.dpo_pay, name='dpo_pay'),
    path('checkout/dpo/callback/', views.dpo_callback, name='dpo_callback'),

    # Orders
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.order_history, name='order_history'),
]
