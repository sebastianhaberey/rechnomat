from decimal import Decimal

from rechnomat.invoice_calc import compute_totals
from rechnomat.model import Invoice

BASE_INVOICE = {
    "customer": "acme-gmbh",
    "issue_date": "2026-08-15",
    "currency": "EUR",
    "line_items": [],
}


def _invoice(line_items: list[dict]) -> Invoice:
    return Invoice.model_validate({**BASE_INVOICE, "line_items": line_items})


def test_compute_totals_single_line_single_rate():
    invoice = _invoice(
        [{"description": "Consulting", "quantity": "8", "unit": "HUR", "unit_price_net": "120.00", "vat_rate": "19"}]
    )

    totals = compute_totals(invoice)

    assert totals.net_total == Decimal("960.00")
    assert len(totals.vat_groups) == 1
    assert totals.vat_groups[0].rate == Decimal("19")
    assert totals.vat_groups[0].net_amount == Decimal("960.00")
    assert totals.vat_groups[0].vat_amount == Decimal("182.40")
    assert totals.vat_total == Decimal("182.40")
    assert totals.gross_total == Decimal("1142.40")


def test_compute_totals_groups_multiple_lines_with_same_rate():
    invoice = _invoice(
        [
            {"description": "A", "quantity": "1", "unit": "EA", "unit_price_net": "100.00", "vat_rate": "19"},
            {"description": "B", "quantity": "1", "unit": "EA", "unit_price_net": "50.00", "vat_rate": "19"},
        ]
    )

    totals = compute_totals(invoice)

    assert len(totals.vat_groups) == 1
    assert totals.vat_groups[0].net_amount == Decimal("150.00")
    assert totals.vat_groups[0].vat_amount == Decimal("28.50")


def test_compute_totals_separates_different_rates_sorted_ascending():
    invoice = _invoice(
        [
            {"description": "Standard", "quantity": "1", "unit": "EA", "unit_price_net": "100.00", "vat_rate": "19"},
            {"description": "Reduced", "quantity": "1", "unit": "EA", "unit_price_net": "100.00", "vat_rate": "7"},
        ]
    )

    totals = compute_totals(invoice)

    assert [group.rate for group in totals.vat_groups] == [Decimal("7"), Decimal("19")]
    assert totals.net_total == Decimal("200.00")
    assert totals.gross_total == Decimal("200.00") + Decimal("7.00") + Decimal("19.00")


def test_compute_totals_separates_exempt_line_from_standard_rate_line():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "notes": "Umsatzsteuerfrei gem. § 3a Abs. 2 UStG, Umkehrung der Steuerschuld",
            "line_items": [
                {
                    "description": "Consulting DE",
                    "quantity": "1",
                    "unit": "EA",
                    "unit_price_net": "100.00",
                    "vat_rate": "19",
                },
                {
                    "description": "Consulting UK",
                    "quantity": "1",
                    "unit": "EA",
                    "unit_price_net": "200.00",
                    "vat_rate": "0",
                    "vat_category_code": "AE",
                },
            ],
        }
    )

    totals = compute_totals(invoice)

    assert len(totals.vat_groups) == 2
    standard_group = next(group for group in totals.vat_groups if group.category_code == "S")
    exempt_group = next(group for group in totals.vat_groups if group.category_code == "AE")
    assert standard_group.rate == Decimal("19")
    assert standard_group.vat_amount == Decimal("19.00")
    assert exempt_group.rate == Decimal("0")
    assert exempt_group.net_amount == Decimal("200.00")
    assert exempt_group.vat_amount == Decimal("0.00")
    assert totals.vat_total == Decimal("19.00")


def test_compute_totals_line_amounts_preserve_order_and_items():
    invoice = _invoice(
        [
            {"description": "First", "quantity": "2", "unit": "EA", "unit_price_net": "10.00", "vat_rate": "19"},
            {"description": "Second", "quantity": "3", "unit": "EA", "unit_price_net": "5.00", "vat_rate": "19"},
        ]
    )

    totals = compute_totals(invoice)

    assert [line.item.description for line in totals.line_amounts] == ["First", "Second"]
    assert [line.net_amount for line in totals.line_amounts] == [Decimal("20.00"), Decimal("15.00")]
