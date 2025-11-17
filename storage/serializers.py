from rest_framework import serializers
from .models import Container, Zone


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ["id", "name", "capacity", "current_load", "type"]


class ContainerSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)
    zone_id = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.all(), source="zone", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Container
        fields = [
            "id",
            "number",
            "type",
            "status",
            "zone",
            "zone_id",
            "arrival_time",
        ]
        read_only_fields = ["id", "arrival_time", "zone", "status"]

    def create(self, validated_data):
        """
        При добавлении контейнера – увеличиваем current_load зоны (если указана).
        """
        zone = validated_data.get("zone")

        if zone:
            # проверка capacity и увеличение current_load
            zone = Zone.objects.select_for_update().get(pk=zone.id)
            if not zone.can_accept(1):
                raise serializers.ValidationError({"detail": "Zone Overloaded"})
            container = Container.objects.create(**validated_data)
            zone.increase_load(1)
        else:
            container = Container.objects.create(**validated_data)

        return container


class ContainerStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = ["status"]

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get("status", old_status)

        # При переходе в SHIPPED – уменьшаем current_load
        if (
            old_status != Container.STATUS_SHIPPED
            and new_status == Container.STATUS_SHIPPED
        ):
            instance.mark_shipped()
        else:
            instance.status = new_status
            instance.save(update_fields=["status"])

        return instance


class AssignContainerSerializer(serializers.Serializer):
    container_id = serializers.IntegerField()

    def validate_container_id(self, value):
        try:
            container = Container.objects.get(pk=value)
        except Container.DoesNotExist:
            raise serializers.ValidationError("Container not found")
        return value
