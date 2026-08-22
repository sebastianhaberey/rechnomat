import importlib.resources

from rechnomat.invoice_html import render_invoice_html
from rechnomat.model import Customer, Invoice, Seller

TEMPLATE_DIR = importlib.resources.files("rechnomat") / "resources" / "templates" / "de-DE"

CUSTOMER = Customer.model_validate(
    {
        "name": "ACME GmbH",
        "address": {"address_line_1": "Musterstrasse 12", "postcode": "10115", "city": "Berlin", "country_code": "DE"},
        "contact": {"name": "Maria Mustermann", "email": "maria@acme.example", "phone": "+49 30 1234567"},
        "invoice_email": "buchhaltung@acme.example",
    }
)

SELLER = Seller.model_validate(
    {
        "name": "Musterfirma Max Mustermann",
        "address": {"address_line_1": "Beispielweg 5", "postcode": "80331", "city": "Muenchen", "country_code": "DE"},
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
)

BASE_INVOICE = {
    "customer": "acme-gmbh",
    "issue_date": "2026-08-15",
    "currency": "EUR",
    "line_items": [
        {"description": "Consulting", "quantity": "8", "unit": "HUR", "unit_price_net": "120.00", "vat_rate": "19"}
    ],
}


def test_render_invoice_html_contains_address_and_info_block():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Musterfirma Max Mustermann · Beispielweg 5 · 80331 Muenchen" in html
    assert "ACME GmbH" in html
    assert "Musterstrasse 12" in html
    assert "10115 Berlin" in html
    assert "Rechnungsnummer" in html
    assert "00000001" in html
    assert "Rechnungsdatum" in html
    assert "15.08.2026" in html


def test_render_invoice_html_omits_country_line_for_domestic_customer():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert ">DE<" not in html


def test_render_invoice_html_includes_country_line_for_non_domestic_customer():
    invoice = Invoice.model_validate(BASE_INVOICE)
    customer = Customer.model_validate(
        {
            "name": "Acme AG",
            "address": {
                "address_line_1": "Bahnhofstrasse 1",
                "postcode": "8001",
                "city": "Zuerich",
                "country_code": "CH",
            },
            "contact": {"name": "Peter Muster", "email": "peter@acme.example", "phone": "+41 44 1234567"},
            "invoice_email": "buchhaltung@acme.example",
        }
    )

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=customer, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert ">CH<" in html


def test_render_invoice_html_omits_optional_info_rows_when_absent():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Zahlbar bis" not in html
    assert "Ihr Zeichen" not in html


def test_render_invoice_html_includes_optional_info_rows_when_present():
    invoice = Invoice.model_validate({**BASE_INVOICE, "payment_terms_days": 14, "buyer_reference": "PO-4711"})

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Zahlbar bis" in html
    assert "29.08.2026" in html
    assert "Ihr Zeichen" in html
    assert "PO-4711" in html
    assert "bis zum <strong>29.08.2026</strong>" in html


def test_render_invoice_html_formats_line_items_and_totals():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                *BASE_INVOICE["line_items"],
                {"description": "Books", "quantity": "2", "unit": "EA", "unit_price_net": "10.00", "vat_rate": "7"},
            ],
        }
    )

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Consulting" in html
    assert "8,00 Std" in html
    assert "120,00 €" in html
    assert "19 %" in html
    assert "960,00 €" in html

    assert "Books" in html
    assert "2,00 Stk" in html
    assert "10,00 €" in html
    assert "7 %" in html
    assert "20,00 €" in html

    assert "Nettosumme" in html
    assert "980,00 €" in html
    assert "zzgl. 19 % USt. auf 960,00 €" in html
    assert "zzgl. 7 % USt. auf 20,00 €" in html
    assert "Gesamtbetrag" in html
    assert "1.163,80 €" in html


def test_render_invoice_html_omits_notes_block_when_absent():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert 'class="notes"' not in html


def test_render_invoice_html_includes_notes_with_paragraph_breaks():
    invoice = Invoice.model_validate({**BASE_INVOICE, "notes": "Erster Absatz.\n\nZweiter Absatz."})

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Erster Absatz.\n\nZweiter Absatz." in html


def test_render_invoice_html_preserves_line_breaks_in_line_item_description():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                {
                    "description": "Consulting\nProjekt Alpha",
                    "quantity": "8",
                    "unit": "HUR",
                    "unit_price_net": "120.00",
                    "vat_rate": "19",
                }
            ],
        }
    )

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Consulting\nProjekt Alpha" in html
    assert '<td class="col-desc">' in html


def test_render_invoice_html_includes_bank_details():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Musterfirma Max Mustermann" in html
    assert "Deutsche Kreditbank" in html
    assert "IBAN DE02120300000000202051" in html
    assert "BIC BYLADEM1001" in html


def test_render_invoice_html_omits_bank_details_when_disabled():
    invoice = Invoice.model_validate({**BASE_INVOICE, "layout": {"render_bank_details": False}})

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert 'class="bank-details"' not in html
    assert "IBAN" not in html


def test_render_invoice_html_omits_notes_when_disabled_even_if_present():
    invoice = Invoice.model_validate({**BASE_INVOICE, "notes": "Vertraulich", "layout": {"render_notes": False}})

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert 'class="notes"' not in html
    assert "Vertraulich" not in html


def test_render_invoice_html_omits_return_address_line_when_disabled():
    invoice = Invoice.model_validate({**BASE_INVOICE, "layout": {"render_return_address_line": False}})

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "Musterfirma Max Mustermann · Beispielweg 5 · 80331 Muenchen" not in html
    assert "Musterstrasse 12" in html


def test_render_invoice_html_embeds_fonts_and_no_external_references():
    invoice = Invoice.model_validate(BASE_INVOICE)

    html = render_invoice_html(
        invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER, template_dir=TEMPLATE_DIR
    )

    assert "data:font/ttf;base64," in html
    assert 'url("fonts/' not in html
