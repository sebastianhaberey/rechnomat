from rechnomat.letter_address import build_address_lines, build_return_address_line
from rechnomat.model import Customer, Seller

CUSTOMER = {
    "name": "ACME GmbH",
    "address": {"street": "Musterstrasse 12", "postcode": "10115", "city": "Berlin", "country_code": "DE"},
    "contact": {"name": "Maria Mustermann", "email": "maria@acme.example", "phone": "+49 30 1234567"},
    "invoice_email": "buchhaltung@acme.example",
}

SELLER = {
    "name": "Musterfirma Max Mustermann",
    "address": {"street": "Beispielweg 5", "postcode": "80331", "city": "Muenchen", "country_code": "DE"},
    "vat_id": "DE987654321",
    "contact": {"name": "Max Mustermann", "email": "max@musterfirma.example", "phone": "+49 89 1234567"},
    "invoice_email": "rechnungen@musterfirma.example",
    "bank_details": {
        "account_owner": "Musterfirma Max Mustermann",
        "iban": "DE02120300000000202051",
        "bic": "BYLADEM1001",
        "bank_name": "Deutsche Kreditbank",
    },
}


def test_build_address_lines_without_legal_form():
    customer = Customer.model_validate(CUSTOMER)
    assert build_address_lines(customer) == ["ACME GmbH", "Musterstrasse 12", "10115 Berlin"]


def test_build_address_lines_appends_legal_form_to_name():
    customer = Customer.model_validate({**CUSTOMER, "legal_form": "GmbH & Co. KG"})
    lines = build_address_lines(customer)
    assert lines[0] == "ACME GmbH GmbH & Co. KG"


def test_build_address_lines_adds_country_for_non_domestic_address():
    customer = Customer.model_validate({**CUSTOMER, "address": {**CUSTOMER["address"], "country_code": "AT"}})
    lines = build_address_lines(customer)
    assert lines[-1] == "AT"


def test_build_address_lines_omits_country_line_for_domestic_address():
    customer = Customer.model_validate(CUSTOMER)
    assert "DE" not in build_address_lines(customer)


def test_build_return_address_line():
    seller = Seller.model_validate(SELLER)
    assert build_return_address_line(seller) == "Musterfirma Max Mustermann · Beispielweg 5 · 80331 Muenchen"
