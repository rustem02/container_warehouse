from django.urls import path
from .consumers import ContainerConsumer

websocket_urlpatterns = [
    path("ws/containers/", ContainerConsumer.as_asgi()),
]
