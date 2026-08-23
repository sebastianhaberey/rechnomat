from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from rechnomat.model import Invoice, LineItem

_CENTS = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class LineItemAmount:
    item: LineItem
    net_amount: Decimal


@dataclass(frozen=True, slots=True)
class VatGroup:
    rate: Decimal
    category_code: str
    net_amount: Decimal
    vat_amount: Decimal


@dataclass(frozen=True, slots=True)
class InvoiceTotals:
    line_amounts: list[LineItemAmount]
    net_total: Decimal
    vat_groups: list[VatGroup]
    vat_total: Decimal
    gross_total: Decimal


def compute_totals(invoice: Invoice) -> InvoiceTotals:
    """
    Compute per-line net amounts and, grouped by VAT category and rate, the net/VAT/gross totals
    for `invoice`.

    VAT is rounded once per group, on that group's summed net amount, rather than per line and
    then summed. This matches the EN 16931 "document totals" tax breakdown (BG-23), which is keyed
    by VAT category and rate rather than by line.
    """
    line_amounts = [
        LineItemAmount(item=item, net_amount=_round(item.quantity * item.unit_price_net)) for item in invoice.line_items
    ]
    net_total = sum((line.net_amount for line in line_amounts), Decimal(0))

    net_by_group: dict[tuple[str, Decimal], Decimal] = {}
    for line in line_amounts:
        key = (line.item.vat_category_code, line.item.vat_rate)
        net_by_group[key] = net_by_group.get(key, Decimal(0)) + line.net_amount

    vat_groups = [
        VatGroup(rate=rate, category_code=category_code, net_amount=net, vat_amount=_round(net * rate / Decimal(100)))
        for (category_code, rate), net in sorted(net_by_group.items(), key=lambda kv: (kv[0][1], kv[0][0]))
    ]
    vat_total = sum((group.vat_amount for group in vat_groups), Decimal(0))

    return InvoiceTotals(
        line_amounts=line_amounts,
        net_total=net_total,
        vat_groups=vat_groups,
        vat_total=vat_total,
        gross_total=net_total + vat_total,
    )


def _round(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)
