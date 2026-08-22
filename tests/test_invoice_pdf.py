import importlib.resources
import io

import pikepdf
import pytest
from facturx import get_xml_from_pdf
from lxml import etree
from pypdf import PdfReader

from rechnomat.invoice_pdf import embed_invoice_xml, render_invoice_pdf
from rechnomat.invoice_xml import build_invoice_xml
from rechnomat.model import Customer, Invoice, Seller

_CII_NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
}

TEMPLATE_DIR = importlib.resources.files("rechnomat") / "resources" / "templates" / "de"
BACKGROUND_PATH = importlib.resources.files("rechnomat") / "resources" / "backgrounds" / "letterhead.pdf"

CUSTOMER = Customer.model_validate(
    {
        "name": "ACME GmbH",
        "address": {"street": "Musterstrasse 12", "postcode": "10115", "city": "Berlin", "country_code": "DE"},
        "contact": {"name": "Maria Mustermann", "email": "maria@acme.example", "phone": "+49 30 1234567"},
        "invoice_email": "buchhaltung@acme.example",
    }
)

SELLER = Seller.model_validate(
    {
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
            "payment_terms_days": 14,
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
            "invoice_email": "buchhaltung@acme.example",
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


def test_render_invoice_pdf_merges_background_behind_content(tmp_path):
    invoice = Invoice.model_validate(BASE_INVOICE)
    output_path = tmp_path / "invoice.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=CUSTOMER,
        seller=SELLER,
        output_path=output_path,
        template_dir=TEMPLATE_DIR,
        background_path=BACKGROUND_PATH,
    )

    background_page = PdfReader(BACKGROUND_PATH).pages[0]
    rendered_page = PdfReader(output_path).pages[0]
    background_xobjects = set(background_page["/Resources"]["/XObject"].keys())
    rendered_xobjects = set(rendered_page["/Resources"]["/XObject"].keys())
    assert background_xobjects <= rendered_xobjects
    # the merged page is the content page (from the @page CSS rule), not the background's stored
    # page - both are A4 but not bit-identical, so compare approximately
    for rendered_value, background_value in zip(rendered_page.mediabox, background_page.mediabox):
        assert rendered_value == pytest.approx(float(background_value), abs=0.01)


def test_render_invoice_pdf_repeats_single_page_background_across_content_pages(tmp_path):
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
        background_path=BACKGROUND_PATH,
    )

    # single-page background must be repeated behind every content page, not collapse them into one
    reader = PdfReader(output_path)
    assert len(reader.pages) > 1
    background_xobjects = set(PdfReader(BACKGROUND_PATH).pages[0]["/Resources"]["/XObject"].keys())
    for page in reader.pages:
        assert background_xobjects <= set(page["/Resources"]["/XObject"].keys())


def test_render_invoice_pdf_writes_pdf_a3_output(tmp_path):
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

    with pikepdf.open(output_path) as pdf:
        assert "/OutputIntents" in pdf.Root
        assert str(pdf.Root.OutputIntents[0].S) == "/GTS_PDFA1"


def test_embed_invoice_xml_produces_retrievable_attachment(tmp_path):
    invoice = Invoice.model_validate(BASE_INVOICE)
    content_path = tmp_path / "content.pdf"

    render_invoice_pdf(
        invoice=invoice,
        invoice_number="00000001",
        customer=CUSTOMER,
        seller=SELLER,
        output_path=content_path,
        template_dir=TEMPLATE_DIR,
    )
    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)

    zugferd_bytes = embed_invoice_xml(content_path.read_bytes(), xml_bytes)

    filename, extracted_xml = get_xml_from_pdf(zugferd_bytes)
    assert filename == "factur-x.xml"
    root = etree.fromstring(extracted_xml)
    invoice_id = root.xpath("//rsm:ExchangedDocument/ram:ID/text()", namespaces=_CII_NS)[0]
    assert invoice_id == "00000001"
    grand_total = root.xpath(
        "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount/text()", namespaces=_CII_NS
    )[0]
    assert grand_total == "1142.40"

    with pikepdf.Pdf.open(io.BytesIO(zugferd_bytes)) as pdf:
        assert "/OutputIntents" in pdf.Root
        assert "/EmbeddedFiles" in pdf.Root.Names
        af_relationships = {str(f.AFRelationship) for f in pdf.Root.AF}
        assert af_relationships == {"/Data"}
