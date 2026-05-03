from decimal import Decimal
from datetime import date, timedelta
from .models import TankVolume, DailyTankSale


def calculate_daily_total(tank, target_date: date) -> Decimal:
    """
    Compute the total sales for a given tank on a given date.

    Sale between two consecutive readings = max(0, prev_volume - curr_volume).

    For the first reading of the day, if a reading exists from the previous day,
    use that as the previous reading. Otherwise, the sale for that first reading is 0.
    """
    today_readings = list(
        TankVolume.objects.filter(
            tank=tank,
            created_at__date=target_date,
            is_archived=False
        ).order_by('created_at')
    )

    if not today_readings:
        return Decimal('0')

    prev_day_reading = (
        TankVolume.objects.filter(
            tank=tank,
            created_at__date=target_date - timedelta(days=1),
            is_archived=False
        ).order_by('created_at').last()
    )

    total_sale = Decimal('0')

    if prev_day_reading:
        diff = prev_day_reading.volume - today_readings[0].volume
        if diff > 0:
            total_sale += diff

    for prev, curr in zip(today_readings, today_readings[1:]):
        diff = prev.volume - curr.volume
        if diff > 0:
            total_sale += diff

    return total_sale


def recalculate_affected_days(tank, target_date: date) -> None:
    """
    Recalculate and persist DailyTankSale for target_date.
    """
    total = calculate_daily_total(tank, target_date)
    DailyTankSale.objects.update_or_create(
        tank=tank,
        date=target_date,
        defaults={'total_sale': total}
    )
