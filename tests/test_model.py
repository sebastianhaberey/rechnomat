from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from rechnomat.model import Address, Customer, Invoice, Layout, Seller

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
}

VALID_SELLER = {
    "name": "Musterfirma Max Mustermann",
    "address": {
        "street": "Beispielweg 5",
        "postcode": "80331",
        "city": "München",
        "country_code": "DE",
    },
    "vat_id": "DE987654321",
    "contact": {
        "name": "Max Mustermann",
        "email": "max.mustermann@musterfirma.example",
        "phone": "+49 89 1234567",
    },
    "bank_details": {
        "account_owner": "Musterfirma Max Mustermann",
        "iban": "DE02120300000000202051",
        "bic": "BYLADEM1001",
        "bank_name": "Deutsche Kreditbank",
    },
}

VALID_INVOICE = {
    "customer": "acme-gmbh",
    "issue_date": "2026-08-15",
    "payment_terms_days": 14,
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
    invoice = Invoice.model_validate({k: v for k, v in VALID_INVOICE.items() if k != "payment_terms_days"})
    assert invoice.due_date is None


def test_invoice_due_date_is_computed_across_year_boundary():
    invoice = Invoice.model_validate({**VALID_INVOICE, "issue_date": "2026-12-20", "payment_terms_days": 30})
    assert invoice.due_date == date(2027, 1, 19)


def test_invoice_layout_defaults_to_de_template_with_everything_rendered():
    invoice = Invoice.model_validate(VALID_INVOICE)
    assert invoice.layout == Layout(
        template="de",
        render_bank_details=True,
        render_notes=True,
        render_address_line=True,
        render_return_address_line=True,
    )


def test_invoice_layout_can_be_overridden():
    invoice = Invoice.model_validate(
        {
            **VALID_INVOICE,
            "layout": {
                "template": "en",
                "render_bank_details": False,
                "render_notes": False,
                "render_address_line": False,
                "render_return_address_line": False,
            },
        }
    )
    assert invoice.layout.template == "en"
    assert invoice.layout.render_bank_details is False
    assert invoice.layout.render_notes is False
    assert invoice.layout.render_address_line is False
    assert invoice.layout.render_return_address_line is False


def test_seller_parses_valid_data():
    seller = Seller.model_validate(VALID_SELLER)
    assert seller.name == "Musterfirma Max Mustermann"
    assert seller.bank_details.account_owner == "Musterfirma Max Mustermann"
    assert seller.bank_details.iban == "DE02120300000000202051"
    assert seller.trade_register is None


def test_seller_accepts_tax_number_instead_of_vat_id():
    without_vat_id = {k: v for k, v in VALID_SELLER.items() if k != "vat_id"}
    seller = Seller.model_validate({**without_vat_id, "tax_number": "143/815/08154"})
    assert seller.vat_id is None
    assert seller.tax_number == "143/815/08154"


def test_seller_requires_vat_id_or_tax_number():
    without_vat_id = {k: v for k, v in VALID_SELLER.items() if k != "vat_id"}
    with pytest.raises(ValidationError):
        Seller.model_validate(without_vat_id)
