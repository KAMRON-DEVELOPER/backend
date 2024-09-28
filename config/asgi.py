import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from community_app.routing import websocket_urlpatterns
from config.middleware import CustomTokenAuthMiddleWare


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": CustomTokenAuthMiddleWare(AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))),
})
