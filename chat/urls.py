from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path("", views.chat_home, name="chat"),
    path('session/<int:product_id>/', views.chat_session, name='chat_session'),
    path('send/', views.send_message, name='send_message'),
    path(
    'ticket-replies/',
    views.ticket_replies,
    name='ticket_replies',
),
    # Support — Track Delivery
path(
    'track-delivery/',
    views.track_delivery,
    name='track_delivery'
),

path(
    'track-delivery/orders/',
    views.track_delivery_orders,
    name='track_delivery_orders'
),

path(
    'track-delivery/order/<int:order_id>/',
    views.track_delivery_order,
    name='track_delivery_order'
),
    path(
    'payment-support/',
    views.payment_support,
    name='payment_support'
),

path(
    'payment-support/orders/',
    views.payment_support_orders,
    name='payment_support_orders'
),
path(
    'payment-support/order/<int:order_id>/',
    views.payment_support_order,
    name='payment_support_order'
),

path(
    'payment-support/order/<int:order_id>/refresh/',
    views.payment_support_refresh,
    name='payment_support_refresh'
),

# Support — Warranty / Technical Issue
    path(
        'warranty-support/',
        views.warranty_support,
        name='warranty_support'
    ),
    path(
    'returns-support/',
    views.returns_support,
    name='returns_support'
),

    path(
    'human-support/',
    views.human_support,
    name='human_support'
),
]



