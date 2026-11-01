"""Tests der Nachbestellempfehlung gemäß Spezifikationsschritt 7."""

from datetime import date

import pytest

from core.reorder import (
    classify_reorder_urgency,
    calculate_reorder_point,
    calculate_reorder_recommendation,
)


def test_calculate_reorder_point_multiplies_trend_by_lead_time() -> None:
    assert calculate_reorder_point(16, 5, 21) == 67.2


def test_calculate_reorder_recommendation_returns_date_from_fixed_today() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=16,
        covered_days=5,
        inventory=120,
        lead_time_days=21,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point == 67.2
    assert result.order_immediately is False
    assert result.days_until_reorder == 16
    assert result.order_date == date(2026, 11, 11)


def test_inventory_equal_to_reorder_point_requires_immediate_order() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=2,
        covered_days=1,
        inventory=20,
        lead_time_days=10,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point == 20
    assert result.order_immediately is True
    assert result.days_until_reorder is None
    assert result.order_date is None


def test_inventory_one_above_reorder_point_orders_today_but_not_immediately() -> None:
    today = date(2026, 10, 26)
    result = calculate_reorder_recommendation(
        total_quantity=2,
        covered_days=1,
        inventory=21,
        lead_time_days=10,
        today=today,
    )

    assert result.order_immediately is False
    assert result.days_until_reorder == 0
    assert result.order_date == today


def test_zero_inventory_requires_immediate_order() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=2,
        covered_days=1,
        inventory=0,
        lead_time_days=10,
        today=date(2026, 10, 26),
    )

    assert result.order_immediately is True
    assert result.days_until_reorder is None
    assert result.order_date is None


def test_inventory_below_reorder_point_requires_immediate_order() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=2,
        covered_days=1,
        inventory=19,
        lead_time_days=10,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point == 20
    assert result.order_immediately is True


def test_zero_lead_time_has_zero_reorder_point() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=2,
        covered_days=1,
        inventory=1,
        lead_time_days=0,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point == 0
    assert result.order_immediately is False
    assert result.days_until_reorder == 0
    assert result.order_date == date(2026, 10, 26)


@pytest.mark.parametrize(
    ("inventory", "lead_time_days", "message"),
    [
        (-1, 10, "Der Lagerbestand muss eine ganze Zahl größer oder gleich 0 sein."),
        (10, -1, "Die Lieferzeit muss eine ganze Zahl größer oder gleich 0 sein."),
    ],
)
def test_negative_inputs_raise_clear_validation_error(
    inventory: int,
    lead_time_days: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        calculate_reorder_recommendation(
            total_quantity=2,
            covered_days=1,
            inventory=inventory,
            lead_time_days=lead_time_days,
            today=date(2026, 10, 26),
        )


def test_zero_trend_returns_no_reorder_point_or_date() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=0,
        covered_days=1,
        inventory=10,
        lead_time_days=10,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point is None
    assert result.order_immediately is False
    assert result.days_until_reorder is None
    assert result.order_date is None


@pytest.mark.parametrize(
    ("total_quantity", "covered_days", "inventory", "lead_time_days", "today"),
    [
        (2, 1, 999_999_999_999_999, 99_999_999, date(2026, 11, 1)),
        (1, 10**15, 999_999_999_999_999, 1, date(2026, 11, 1)),
        (1, 1, 3, 0, date.max),
    ],
)
def test_unrepresentable_order_date_returns_recommendation_without_date(
    total_quantity: int,
    covered_days: int,
    inventory: int,
    lead_time_days: int,
    today: date,
) -> None:
    result = calculate_reorder_recommendation(
        total_quantity=total_quantity,
        covered_days=covered_days,
        inventory=inventory,
        lead_time_days=lead_time_days,
        today=today,
    )

    assert result.order_immediately is False
    assert result.days_until_reorder is not None
    assert result.order_date is None


def test_decimal_trend_does_not_create_false_immediate_order() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=1,
        covered_days=10,
        inventory=1,
        lead_time_days=3,
        today=date(2026, 10, 26),
    )

    assert result.reorder_point == 0.3
    assert result.order_immediately is False
    assert result.days_until_reorder == 7
    assert result.order_date == date(2026, 11, 2)


def test_fractional_trend_calculates_exact_days_and_date() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=200,
        covered_days=90,
        inventory=120,
        lead_time_days=21,
        today=date(2026, 11, 1),
    )

    assert result.days_until_reorder == 33
    assert result.order_date == date(2026, 12, 4)


def test_inventory_equal_to_fractional_reorder_point_orders_immediately() -> None:
    result = calculate_reorder_recommendation(
        total_quantity=200,
        covered_days=90,
        inventory=20,
        lead_time_days=9,
        today=date(2026, 11, 1),
    )

    assert result.order_immediately is True
    assert result.days_until_reorder is None


def test_inventory_just_above_fractional_reorder_point_orders_today() -> None:
    today = date(2026, 11, 1)
    result = calculate_reorder_recommendation(
        total_quantity=200,
        covered_days=90,
        inventory=21,
        lead_time_days=9,
        today=today,
    )

    assert result.order_immediately is False
    assert result.days_until_reorder == 0
    assert result.order_date == today


@pytest.mark.parametrize(
    ("total_quantity", "covered_days", "inventory", "lead_time_days", "expected_days"),
    [
        (200, 90, 100, 9, 36),
        (7, 2, 49, 4, 10),
        (3, 2, 18, 2, 10),
    ],
)
def test_reorder_days_are_exact_for_integer_boundaries(
    total_quantity: int,
    covered_days: int,
    inventory: int,
    lead_time_days: int,
    expected_days: int,
) -> None:
    result = calculate_reorder_recommendation(
        total_quantity=total_quantity,
        covered_days=covered_days,
        inventory=inventory,
        lead_time_days=lead_time_days,
        today=date(2026, 11, 1),
    )

    assert result.days_until_reorder == expected_days


@pytest.mark.parametrize(
    ("days_until_reorder", "expected"),
    [
        (0, "critical"),
        (2, "critical"),
        (3, "warning"),
        (7, "warning"),
        (8, "ok"),
    ],
)
def test_classify_reorder_urgency_at_threshold_boundaries(
    days_until_reorder: int,
    expected: str,
) -> None:
    assert (
        classify_reorder_urgency(
            days_until_reorder=days_until_reorder,
            inventory=100,
            reorder_point=20,
        )
        == expected
    )


@pytest.mark.parametrize("inventory", [19, 20])
def test_inventory_at_or_below_reorder_point_is_critical(inventory: int) -> None:
    assert (
        classify_reorder_urgency(
            days_until_reorder=None,
            inventory=inventory,
            reorder_point=20,
        )
        == "critical"
    )


def test_classify_reorder_urgency_returns_none_without_reorder_point() -> None:
    assert (
        classify_reorder_urgency(
            days_until_reorder=None,
            inventory=100,
            reorder_point=None,
        )
        is None
    )
