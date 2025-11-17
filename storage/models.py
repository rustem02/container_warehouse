from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError


class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField()
    current_load = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.current_load}/{self.capacity})"

    def can_accept(self, delta: int = 1) -> bool:
        """Проверяем, влезет ли ещё delta контейнеров."""
        return self.current_load + delta <= self.capacity

    def increase_load(self, delta: int = 1):
        if not self.can_accept(delta):
            raise ValidationError("Zone Overloaded")
        self.current_load += delta
        self.save(update_fields=["current_load"])

    def decrease_load(self, delta: int = 1):
        if self.current_load >= delta:
            self.current_load -= delta
        else:
            self.current_load = 0
        self.save(update_fields=["current_load"])


class Container(models.Model):
    STATUS_WAITING = "waiting"
    STATUS_STORED = "stored"
    STATUS_SHIPPED = "shipped"

    STATUS_CHOICES = [
        (STATUS_WAITING, "Waiting"),
        (STATUS_STORED, "Stored"),
        (STATUS_SHIPPED, "Shipped"),
    ]

    number = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING
    )
    zone = models.ForeignKey(
        Zone, related_name="containers", null=True, blank=True, on_delete=models.SET_NULL
    )
    arrival_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.number} ({self.status})"

    @transaction.atomic
    def assign_to_zone(self, zone: Zone):
        """
        Разместить контейнер в зоне:
        - уменьшаем current_load старой зоны
        - увеличиваем current_load новой зоны
        """
        if self.zone_id == zone.id:
            return  # уже в этой зоне

        # освободить старую зону
        if self.zone:
            old_zone = Zone.objects.select_for_update().get(pk=self.zone_id)
            old_zone.decrease_load(1)

        # занять новую зону
        zone = Zone.objects.select_for_update().get(pk=zone.id)
        if not zone.can_accept(1):
            raise ValidationError("Zone Overloaded")

        zone.increase_load(1)
        self.zone = zone
        self.status = self.STATUS_STORED
        self.save(update_fields=["zone", "status"])

    @transaction.atomic
    def mark_shipped(self):
        """
        Отгрузка контейнера:
        - уменьшаем current_load зоны
        - меняем статус на SHIPPED
        - по желанию можно отвязать зону
        """
        if self.zone:
            zone = Zone.objects.select_for_update().get(pk=self.zone_id)
            zone.decrease_load(1)
            self.zone = None

        self.status = self.STATUS_SHIPPED
        self.save(update_fields=["status", "zone"])
