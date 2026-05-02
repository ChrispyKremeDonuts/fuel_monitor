from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Q


class Location(models.Model):
    name = models.CharField(max_length=255)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class Tank(models.Model):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tanks')
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name


class TankVolume(models.Model):
    tank = models.ForeignKey(Tank, on_delete=models.CASCADE, related_name='volumes')
    volume = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField()
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(check=Q(volume__gte=0), name='volume_non_negative')
        ]

    def __str__(self):
        return f"Tank {self.tank_id} @ {self.created_at}: {self.volume}"


