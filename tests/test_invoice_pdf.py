import importlib.resources

from pypdf import PdfReader

from rechnomat.invoice_pdf import render_invoice_pdf
from rechnomat.model import Customer, Invoice, Seller

TEMPLATE_DIR = importlib.resources.files("rechnomat") / "resources" / "templates" / "de"

CUSTOMER = Customer.model_validate(
    {
        "name": "ACME GmbH",
        "address": {"street": "Musterstrasse 12", "postcode": "10115", "city": "Berlin", "country_code": "DE"},
        "contact": {"name": "Maria Mustermann", "email": "maria@acme.example", "phone": "+49 30 1234567"},
        "payment_terms_days": 14,
    }
)

SELLER = Seller.model_validate(
    {
        "name": "Musterfirma Max Mustermann",
        "address": {"street": "Beispielweg 5", "postcode": "80331", "city": "Muenchen", "country_code": "DE"},
        "vat_id": "DE987654321",
        "contact": {"name": "Max Mustermann", "email": "max@musterfirma.example", "phone": "+49 89 1234567"},
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


def test_render_invoice_pdf_writes_valid_pdf_file(tmp_path):
    invoice = Invoice.model_validate(BASE_INVOICE)
    output_path = tmp_path / "invoice.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=CUSTOMER,
        seller=SELLER,
        output_path=output_path,
        template_dir=TEMPLATE_DIR,
    )

    assert output_path.read_bytes().startswith(b"%PDF-")


def test_render_invoice_pdf_handles_multiple_vat_rates_and_optional_fields(tmp_path):
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "due_date": "2026-08-29",
            "buyer_reference": "PO-4711",
            "notes": "Vielen Dank für die gute Zusammenarbeit.",
            "line_items": [
                *BASE_INVOICE["line_items"],
                {
                    "description": "Books",
                    "quantity": "2",
                    "unit": "EA",
                    "unit_price_net": "10.00",
                    "vat_rate": "7",
                },
            ],
        }
    )
    output_path = tmp_path / "invoice.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=CUSTOMER,
        seller=SELLER,
        output_path=output_path,
        template_dir=TEMPLATE_DIR,
    )

    assert output_path.read_bytes().startswith(b"%PDF-")


def test_render_invoice_pdf_handles_non_domestic_customer_address(tmp_path):
    invoice = Invoice.model_validate(BASE_INVOICE)
    customer = Customer.model_validate(
        {
            "name": "Acme AG",
            "address": {"street": "Bahnhofstrasse 1", "postcode": "8001", "city": "Zuerich", "country_code": "CH"},
            "contact": {"name": "Peter Muster", "email": "peter@acme.example", "phone": "+41 44 1234567"},
            "payment_terms_days": 30,
        }
    )
    output_path = tmp_path / "invoice.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=customer,
        seller=SELLER,
        output_path=output_path,
        template_dir=TEMPLATE_DIR,
    )

    assert output_path.read_bytes().startswith(b"%PDF-")


def test_render_invoice_pdf_paginates_when_content_overflows_a_single_page(tmp_path):
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                {
                    "description": f"Beratungsleistung Position {i}",
                    "quantity": "1",
                    "unit": "HUR",
                    "unit_price_net": "100.00",
                    "vat_rate": "19",
                }
                for i in range(80)
            ],
        }
    )
    output_path = tmp_path / "invoice.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=CUSTOMER,
        seller=SELLER,
        output_path=output_path,
        template_dir=TEMPLATE_DIR,
    )

    assert len(PdfReader(output_path).pages) > 1
