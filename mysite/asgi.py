import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "mysite.settings",
)


django_application = get_asgi_application()


from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter(
    {
        "http": django_application,

        "websocket": AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ),
    }
)