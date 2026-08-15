from reportlab.pdfbase.pdfmetrics import stringWidth

from rechnomat.invoice_calc import compute_totals
from rechnomat.invoice_pdf import (
    BODY_FONT_SIZE,
    COL_DESC_X,
    FONT_REGULAR,
    _Cursor,
    _draw_line_items_table,
    render_invoice_pdf,
)
from rechnomat.model import Customer, Invoice, Seller

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
        "bank_details": {"iban": "DE02120300000000202051", "bic": "BYLADEM1001", "bank_name": "Deutsche Kreditbank"},
    }
)

BASE_INVOICE = {
    "invoice_number": "00000001",
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

    render_invoice_pdf(invoice=invoice, customer=CUSTOMER, seller=SELLER, output_path=output_path)

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

    render_invoice_pdf(invoice=invoice, customer=CUSTOMER, seller=SELLER, output_path=output_path)

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

    render_invoice_pdf(invoice=invoice, customer=customer, seller=SELLER, output_path=output_path)

    assert output_path.read_bytes().startswith(b"%PDF-")


class _RecordingCanvas:
    def __init__(self):
        self.draw_string_calls = []
        self.draw_right_string_calls = []

    def setFont(self, font, size):
        pass

    def setLineWidth(self, width):
        pass

    def line(self, x1, y1, x2, y2):
        pass

    def drawString(self, x, y, text):
        self.draw_string_calls.append((x, y, text))

    def drawRightString(self, x, y, text):
        self.draw_right_string_calls.append((x, y, text))


def _item_description_lines(canvas):
    return [text for x, y, text in canvas.draw_string_calls if x == COL_DESC_X and text != "Beschreibung"]


def test_draw_line_items_table_wraps_long_description_onto_multiple_lines():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                {
                    "description": "Beratungsleistungen im Rahmen der Systemarchitektur, "
                    "einschliesslich Anforderungsanalyse, Dokumentation und Abstimmung mit dem Kunden",
                    "quantity": "8",
                    "unit": "HUR",
                    "unit_price_net": "120.00",
                    "vat_rate": "19",
                }
            ],
        }
    )
    totals = compute_totals(invoice)
    canvas = _RecordingCanvas()
    cursor = _Cursor(canvas=canvas, y=0)

    _draw_line_items_table(cursor, invoice, totals)

    item_description_lines = _item_description_lines(canvas)
    assert len(item_description_lines) > 1
    assert " ".join(item_description_lines) == invoice.line_items[0].description
    # Quantity/price/VAT/amount are only drawn once per line item, not once per wrapped description line.
    header_right_string_calls = 4
    item_right_string_calls = 4
    assert len(canvas.draw_right_string_calls) == header_right_string_calls + item_right_string_calls

    quantity_x, _, quantity_text = canvas.draw_right_string_calls[header_right_string_calls]
    quantity_start_x = quantity_x - stringWidth(quantity_text, FONT_REGULAR, BODY_FONT_SIZE)
    first_line_width = stringWidth(item_description_lines[0], FONT_REGULAR, BODY_FONT_SIZE)
    assert COL_DESC_X + first_line_width < quantity_start_x


def test_draw_line_items_table_keeps_short_description_on_single_line():
    invoice = Invoice.model_validate(BASE_INVOICE)
    totals = compute_totals(invoice)
    canvas = _RecordingCanvas()
    cursor = _Cursor(canvas=canvas, y=0)

    _draw_line_items_table(cursor, invoice, totals)

    item_description_lines = _item_description_lines(canvas)
    assert item_description_lines == [invoice.line_items[0].description]
