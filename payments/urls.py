# payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # single product payment
    path('dpo_payment/<int:product_id>/', views.dpo_payment, name='dpo_payment'),
    
    # full cart payment (no product id)
    path('dpo_payment/', views.dpo_payment, name='dpo_payment_cart'),

    # payment callback
    path('dpo_callback/', views.dpo_callback, name='dpo_callback'),
]
