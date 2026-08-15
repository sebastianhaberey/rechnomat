from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from rechnomat.model import Address, Customer, Invoice

VALID_CUSTOMER = {
    "name": "ACME GmbH",
    "address": {
        "street": "Musterstraße 12",
        "postcode": "10115",
        "city": "Berlin",
        "country_code": "DE",
    },
    "vat_id": "DE123456789",
    "contact": {
        "name": "Maria Mustermann",
        "email": "maria.mustermann@acme-gmbh.example",
        "phone": "+49 30 1234567",
    },
    "payment_terms_days": 14,
}

VALID_INVOICE = {
    "invoice_number": "0000000",
    "customer": "acme-gmbh",
    "issue_date": "2026-08-15",
    "due_date": "2026-08-29",
    "currency": "EUR",
    "line_items": [
        {
            "description": "Consulting services, August 2026",
            "quantity": 8,
            "unit": "HUR",
            "unit_price_net": "120.00",
            "vat_rate": 19,
        },
    ],
}


def test_customer_parses_valid_data():
    customer = Customer.model_validate(VALID_CUSTOMER)
    assert customer.name == "ACME GmbH"
    assert customer.address.country_code == "DE"
    assert customer.legal_form is None
    assert customer.notes is None


def test_customer_rejects_invalid_country_code():
    invalid = {**VALID_CUSTOMER, "address": {**VALID_CUSTOMER["address"], "country_code": "Germany"}}
    with pytest.raises(ValidationError):
        Address.model_validate(invalid["address"])


def test_invoice_parses_valid_data():
    invoice = Invoice.model_validate(VALID_INVOICE)
    assert invoice.invoice_number == "0000000"
    assert invoice.issue_date == date(2026, 8, 15)
    assert invoice.due_date == date(2026, 8, 29)
    assert len(invoice.line_items) == 1
    assert invoice.line_items[0].unit_price_net == Decimal("120.00")


def test_invoice_unit_price_is_exact_decimal_when_quoted():
    invoice = Invoice.model_validate(VALID_INVOICE)
    # Exact decimal arithmetic, no binary float rounding error.
    assert invoice.line_items[0].unit_price_net * invoice.line_items[0].quantity == Decimal("960.00")


def test_invoice_rejects_invalid_currency():
    invalid = {**VALID_INVOICE, "currency": "Euro"}
    with pytest.raises(ValidationError):
        Invoice.model_validate(invalid)


def test_invoice_requires_line_items():
    invalid = {k: v for k, v in VALID_INVOICE.items() if k != "line_items"}
    with pytest.raises(ValidationError):
        Invoice.model_validate(invalid)


def test_invoice_due_date_is_optional():
    invoice = Invoice.model_validate({k: v for k, v in VALID_INVOICE.items() if k != "due_date"})
    assert invoice.due_date is None
