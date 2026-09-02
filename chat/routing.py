from django.urls import path

from .consumers import HumanSupportConsumer


websocket_urlpatterns = [
    path(
        "ws/human-support/<int:ticket_id>/",
        HumanSupportConsumer.as_asgi(),
    ),
]