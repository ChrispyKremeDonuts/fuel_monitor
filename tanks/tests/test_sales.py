import pytest
from datetime import date
from decimal import Decimal
from tanks.services import calculate_daily_total
from .conftest import make_reading


# ---------------------------------------------------------------------------
# Basic sale calculation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_no_readings_returns_zero(tank_a):
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_single_reading_no_prior_day_returns_zero(tank_a):
    make_reading(tank_a, 50, "2023-01-02 10:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_volume_decrease_is_sale(tank_a):
    make_reading(tank_a, 30, "2023-01-02 10:00")
    make_reading(tank_a, 10, "2023-01-02 11:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('20')


@pytest.mark.django_db
def test_volume_increase_is_zero_sale(tank_a):
    make_reading(tank_a, 10, "2023-01-02 10:00")
    make_reading(tank_a, 30, "2023-01-02 11:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_volume_same_is_zero_sale(tank_a):
    make_reading(tank_a, 20, "2023-01-02 10:00")
    make_reading(tank_a, 20, "2023-01-02 11:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_volume_drops_to_zero(tank_a):
    make_reading(tank_a, 15, "2023-01-02 10:00")
    make_reading(tank_a, 0, "2023-01-02 11:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('15')


@pytest.mark.django_db
def test_refill_mid_day_treated_as_zero_sale(tank_a):
    """A spike upward (refill) should not produce negative sale."""
    make_reading(tank_a, 50, "2023-01-02 09:00")
    make_reading(tank_a, 10, "2023-01-02 10:00")
    make_reading(tank_a, 90, "2023-01-02 11:00")
    make_reading(tank_a, 80, "2023-01-02 12:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('50')


# ---------------------------------------------------------------------------
# Archived readings are excluded
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_archived_reading_excluded_from_daily_total(tank_a):
    reading = make_reading(tank_a, 30, "2023-01-02 10:00")
    make_reading(tank_a, 10, "2023-01-02 11:00")
    reading.is_archived = True
    reading.save()
    total = calculate_daily_total(tank_a, date(2023, 1, 2))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_archived_prev_day_reading_excluded_from_cross_day(tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 23:00")
    make_reading(tank_a, 30, "2023-01-03 08:00")
    reading.is_archived = True
    reading.save()
    total = calculate_daily_total(tank_a, date(2023, 1, 3))
    assert total == Decimal('0')


# ---------------------------------------------------------------------------
# Cross-day calculation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cross_day_decrease(tank_a):
    """Last reading of prev day is higher → sale on first reading of next day."""
    make_reading(tank_a, 50, "2023-01-02 23:00")
    make_reading(tank_a, 30, "2023-01-03 08:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 3))
    assert total == Decimal('20')


@pytest.mark.django_db
def test_cross_day_increase_is_zero(tank_a):
    """Last reading of prev day is lower → first reading of next day is a refill → sale = 0."""
    make_reading(tank_a, 20, "2023-01-02 23:00")
    make_reading(tank_a, 40, "2023-01-03 08:00")
    total = calculate_daily_total(tank_a, date(2023, 1, 3))
    assert total == Decimal('0')


@pytest.mark.django_db
def test_multi_day_gap(tank_a):
    """No readings on Jan 3 — first reading on Jan 4 looks back to Jan 3 (none), so sale = 0."""
    make_reading(tank_a, 60, "2023-01-02 20:00")
    make_reading(tank_a, 40, "2023-01-04 10:00")
    total_jan4 = calculate_daily_total(tank_a, date(2023, 1, 4))
    assert total_jan4 == Decimal('0')

