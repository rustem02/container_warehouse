from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Container, Zone
from .serializers import (
    ContainerSerializer,
    ContainerStatusUpdateSerializer,
    ZoneSerializer,
    AssignContainerSerializer,
)


def send_container_event(event_type: str, container: Container):
    """
    Отправка WebSocket-события в группу "containers".
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        "containers",
        {
            "type": "container_event",
            "event": event_type,
            "data": {
                "id": container.id,
                "number": container.number,
                "status": container.status,
                "zone_id": container.zone_id,
            },
        },
    )


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all().order_by("id")
    serializer_class = ContainerSerializer

    http_method_names = ["get", "post", "patch", "head", "options"]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            response = super().create(request, *args, **kwargs)
            if response.status_code == status.HTTP_201_CREATED:
                container = Container.objects.get(pk=response.data["id"])
                send_container_event("created", container)
            return response

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /containers/:id — обновление статуса.
        """
        container = self.get_object()
        serializer = ContainerStatusUpdateSerializer(
            container, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
            container.refresh_from_db()
            send_container_event("updated", container)

        return Response(ContainerSerializer(container).data)


class ZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /zones — список зон
    POST /zones/:id/assign — разместить контейнер в зону (с проверкой capacity)
    """

    queryset = Zone.objects.all().order_by("id")
    serializer_class = ZoneSerializer

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        zone = self.get_object()
        serializer = AssignContainerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container_id = serializer.validated_data["container_id"]

        container = get_object_or_404(Container, pk=container_id)

        with transaction.atomic():
            try:
                container.assign_to_zone(zone)
            except Exception as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

        send_container_event("assigned", container)
        return Response(ContainerSerializer(container).data, status=status.HTTP_200_OK)
