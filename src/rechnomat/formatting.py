from datetime import date
from decimal import ROUND_HALF_UP, Decimal

_CURRENCY_SYMBOLS = {"EUR": "€"}


def format_decimal_de(value: Decimal, *, decimals: int = 2) -> str:
    """
    Format a Decimal using German number conventions: comma as decimal separator, period as thousands
    separator, rounded half-up to `decimals` places.
    """
    quantized = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    text = f"{quantized:,.{decimals}f}"
    # swap "," (thousands) and "." (decimal) via a placeholder, so the second substitution can't
    # re-match characters produced by the first
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_amount(value: Decimal, currency: str) -> str:
    """
    Format a monetary amount with German number formatting, suffixed with a currency symbol for known
    currencies or the raw ISO 4217 code otherwise.
    """
    suffix = _CURRENCY_SYMBOLS.get(currency, currency)
    return f"{format_decimal_de(value)} {suffix}"


def format_percent(value: Decimal) -> str:
    """
    Format a percentage, dropping a trailing ",00" for whole numbers (e.g. "19 %" not "19,00 %").
    """
    text = format_decimal_de(value)
    if text.endswith(",00"):
        text = text[:-3]
    return f"{text} %"


def format_date_de(value: date) -> str:
    return value.strftime("%d.%m.%Y")
