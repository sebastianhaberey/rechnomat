from datetime import date
from decimal import Decimal

from rechnomat.formatting import format_amount, format_date_de, format_decimal_de, format_percent


def test_format_decimal_de_uses_comma_as_decimal_separator():
    assert format_decimal_de(Decimal("120.5")) == "120,50"


def test_format_decimal_de_uses_period_as_thousands_separator():
    assert format_decimal_de(Decimal("1234567.89")) == "1.234.567,89"


def test_format_decimal_de_rounds_half_up():
    assert format_decimal_de(Decimal("1.005")) == "1,01"


def test_format_amount_appends_euro_symbol():
    assert format_amount(Decimal("42"), "EUR") == "42,00 €"


def test_format_amount_falls_back_to_iso_code_for_unknown_currency():
    assert format_amount(Decimal("42"), "USD") == "42,00 USD"


def test_format_percent_drops_trailing_zero_decimals():
    assert format_percent(Decimal("19")) == "19 %"
    assert format_percent(Decimal("19.00")) == "19 %"


def test_format_percent_keeps_nonzero_decimals():
    assert format_percent(Decimal("7.5")) == "7,50 %"


def test_format_date_de_uses_german_day_month_year_order():
    assert format_date_de(date(2026, 8, 15)) == "15.08.2026"
