import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guitarshop.settings')

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()  # ← must be called before any other django imports

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from products import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})