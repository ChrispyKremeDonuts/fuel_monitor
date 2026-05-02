import pytest
from datetime import datetime, timezone
from decimal import Decimal
from tanks.models import Location, Tank, TankVolume


@pytest.fixture
def location(db):
    return Location.objects.create(name="Austin, TX")


@pytest.fixture
def tank_a(db, location):
    return Tank.objects.create(name="Tank A", location=location)


@pytest.fixture
def tank_b(db, location):
    return Tank.objects.create(name="Tank B", location=location)


def make_reading(tank, volume, dt_str):
    """Helper: create a TankVolume with a naive datetime string like '2023-01-02 10:00'."""
    dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
    return TankVolume.objects.create(tank=tank, volume=Decimal(str(volume)), created_at=dt)


