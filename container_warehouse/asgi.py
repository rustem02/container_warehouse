import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from .routing import application as channels_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "container_warehouse.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # websocket – уже описан в warehouse.routing
        "websocket": channels_application.application_mapping["websocket"],
    }
)
