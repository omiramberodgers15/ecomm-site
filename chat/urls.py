from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('session/<int:product_id>/', views.chat_session, name='chat_session'),
    path('send/', views.send_message, name='send_message'),
]
