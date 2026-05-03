from datetime import datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand

from tanks.models import DailyTankSale, Location, Tank, TankVolume
from tanks.services import recalculate_affected_days


class Command(BaseCommand):
    help = 'Seed the database with sample fuel monitoring data'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        TankVolume.objects.all().delete()
        DailyTankSale.objects.all().delete()
        Tank.objects.all().delete()
        Location.objects.all().delete()

        self.stdout.write('Creating locations and tanks...')
        austin = Location.objects.create(name='Austin, TX')
        houston = Location.objects.create(name='Houston, TX')

        tank_a = Tank.objects.create(name='Tank A', location=austin)
        tank_b = Tank.objects.create(name='Tank B', location=austin)
        tank_c = Tank.objects.create(name='Tank C', location=houston)

        def r(volume, dt_str):
            return (Decimal(str(volume)), datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc))

        # Week of Jan 1-5 2024 (Mon-Fri)
        # Volumes drop throughout each day; refills visible as spikes upward
        tank_readings = {
            tank_a: [
                r(500, '2024-01-01T08:00:00'),
                r(450, '2024-01-01T20:00:00'),
                r(420, '2024-01-02T08:00:00'),
                r(380, '2024-01-02T20:00:00'),
                r(350, '2024-01-03T08:00:00'),
                r(300, '2024-01-03T20:00:00'),
                r(800, '2024-01-04T08:00:00'),  # refill
                r(740, '2024-01-04T20:00:00'),
                r(700, '2024-01-05T08:00:00'),
                r(650, '2024-01-05T20:00:00'),
            ],
            tank_b: [
                r(300, '2024-01-01T09:00:00'),
                r(270, '2024-01-01T21:00:00'),
                r(240, '2024-01-02T09:00:00'),
                r(200, '2024-01-02T21:00:00'),
                r(600, '2024-01-03T09:00:00'),  # refill
                r(560, '2024-01-03T21:00:00'),
                r(520, '2024-01-04T09:00:00'),
                r(480, '2024-01-04T21:00:00'),
                r(440, '2024-01-05T09:00:00'),
                r(400, '2024-01-05T21:00:00'),
            ],
            tank_c: [
                r(1000, '2024-01-01T07:00:00'),
                r(900,  '2024-01-01T19:00:00'),
                r(850,  '2024-01-02T07:00:00'),
                r(750,  '2024-01-02T19:00:00'),
                r(700,  '2024-01-03T07:00:00'),
                r(600,  '2024-01-03T19:00:00'),
                r(550,  '2024-01-04T07:00:00'),
                r(450,  '2024-01-04T19:00:00'),
                r(1500, '2024-01-05T07:00:00'),  # refill
                r(1400, '2024-01-05T19:00:00'),
            ],
        }

        self.stdout.write('Creating readings and recalculating daily sales...')
        for tank, readings in tank_readings.items():
            for volume, created_at in readings:
                TankVolume.objects.create(tank=tank, volume=volume, created_at=created_at)
            for d in sorted({created_at.date() for _, created_at in readings}):
                recalculate_affected_days(tank, d)

        self.stdout.write(self.style.SUCCESS('\nDone! Try these running average queries:'))
        self.stdout.write(f'\n  Tank A (id={tank_a.id}) — Austin, TX')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_a.id}&date=2024-01-01  →  50.00')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_a.id}&date=2024-01-02  →  60.00')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_a.id}&date=2024-01-03  →  66.67')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_a.id}&date=2024-01-04  →  65.00')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_a.id}&date=2024-01-05  →  70.00')
        self.stdout.write(f'\n  Tank B (id={tank_b.id}) — Austin, TX')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_b.id}&date=2024-01-05  →  60.00')
        self.stdout.write(f'\n  Tank C (id={tank_c.id}) — Houston, TX')
        self.stdout.write(f'    /api/running-average/?tank_id={tank_c.id}&date=2024-01-05  →  130.00')
