from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from rechnomat.formatting import format_amount, format_date_de, format_decimal_de, format_percent, format_unit_de
from rechnomat.invoice_calc import InvoiceTotals, compute_totals
from rechnomat.letter_address import build_address_lines, build_return_address_line
from rechnomat.model import Customer, Invoice, Seller

PAGE_WIDTH, PAGE_HEIGHT = A4

# DIN 5008 Form A reference points (approximate standard values for a C6/5 windowed envelope),
# measured from the top-left corner of the page. Not yet verified against a real envelope/printer —
# revisit once the letterhead background is added.
FOLD_MARK_1 = 105 * mm
FOLD_MARK_2 = 210 * mm
PUNCH_MARK = 148.5 * mm
MARK_LENGTH = 5 * mm

LEFT_MARGIN = 25 * mm
RIGHT_MARGIN = 20 * mm
CONTENT_RIGHT = PAGE_WIDTH - RIGHT_MARGIN
CONTENT_WIDTH = CONTENT_RIGHT - LEFT_MARGIN

ADDRESS_FIELD_LEFT = 20 * mm
ADDRESS_FIELD_TOP = 45 * mm
RETURN_ADDRESS_ZONE_HEIGHT = 5 * mm

INFO_BLOCK_LEFT = 125 * mm
INFO_BLOCK_TOP = 32 * mm
INFO_BLOCK_ROW_HEIGHT = 9 * mm

BODY_TOP = 98 * mm

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
BODY_FONT_SIZE = 10
SMALL_FONT_SIZE = 7
LINE_HEIGHT = 4.5 * mm

COL_DESC_X = LEFT_MARGIN
COL_QTY_X = LEFT_MARGIN + 95 * mm
COL_PRICE_X = LEFT_MARGIN + 125 * mm
COL_VAT_X = LEFT_MARGIN + 145 * mm
COL_AMOUNT_X = CONTENT_RIGHT

DESC_COL_GAP = 5 * mm


def render_invoice_pdf(*, invoice: Invoice, customer: Customer, seller: Seller, output_path: Path) -> None:
    """
    Render `invoice` as a DIN 5008 Form A letter PDF: address field, letter body with line items and
    totals. No letterhead background or embedded EN 16931 XML yet - both are added in later steps.
    """
    canvas = Canvas(str(output_path), pagesize=A4, pageCompression=0)
    _draw_fold_and_punch_marks(canvas)
    _draw_address_field(canvas, customer=customer, seller=seller)
    _draw_info_block(canvas, invoice=invoice)
    _draw_body(canvas, invoice=invoice, seller=seller)
    canvas.showPage()
    canvas.save()


def _y_from_top(distance_from_top: float) -> float:
    return PAGE_HEIGHT - distance_from_top


def _draw_fold_and_punch_marks(canvas: Canvas) -> None:
    canvas.setLineWidth(0.3)
    for distance in (FOLD_MARK_1, PUNCH_MARK, FOLD_MARK_2):
        y = _y_from_top(distance)
        canvas.line(0, y, MARK_LENGTH, y)


def _draw_address_field(canvas: Canvas, *, customer: Customer, seller: Seller) -> None:
    field_top_y = _y_from_top(ADDRESS_FIELD_TOP)

    return_line = build_return_address_line(seller)
    return_y = field_top_y - RETURN_ADDRESS_ZONE_HEIGHT + 1.5 * mm
    canvas.setFont(FONT_REGULAR, SMALL_FONT_SIZE)
    canvas.drawString(ADDRESS_FIELD_LEFT, return_y, return_line)
    text_width = canvas.stringWidth(return_line, FONT_REGULAR, SMALL_FONT_SIZE)
    canvas.setLineWidth(0.3)
    canvas.line(ADDRESS_FIELD_LEFT, return_y - 1, ADDRESS_FIELD_LEFT + text_width, return_y - 1)

    address_y = field_top_y - RETURN_ADDRESS_ZONE_HEIGHT - 4 * mm
    canvas.setFont(FONT_REGULAR, BODY_FONT_SIZE)
    for line in build_address_lines(customer):
        canvas.drawString(ADDRESS_FIELD_LEFT, address_y, line)
        address_y -= LINE_HEIGHT


def _draw_info_block(canvas: Canvas, *, invoice: Invoice) -> None:
    rows = [("Rechnungsnummer", invoice.invoice_number), ("Rechnungsdatum", format_date_de(invoice.issue_date))]
    if invoice.due_date:
        rows.append(("Zahlbar bis", format_date_de(invoice.due_date)))
    if invoice.buyer_reference:
        rows.append(("Ihr Zeichen", invoice.buyer_reference))

    y = _y_from_top(INFO_BLOCK_TOP)
    for label, value in rows:
        canvas.setFont(FONT_REGULAR, SMALL_FONT_SIZE)
        canvas.drawString(INFO_BLOCK_LEFT, y, label)
        canvas.setFont(FONT_REGULAR, BODY_FONT_SIZE)
        canvas.drawString(INFO_BLOCK_LEFT, y - 3.8 * mm, value)
        y -= INFO_BLOCK_ROW_HEIGHT


def wrap_text(text: str, *, font: str, size: float, max_width: float) -> list[str]:
    """
    Greedily word-wrap `text` into lines that each fit within `max_width` at the given font/size.
    """
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


@dataclass
class _Cursor:
    canvas: Canvas
    y: float

    def text(self, s: str, *, font: str = FONT_REGULAR, size: float = BODY_FONT_SIZE) -> None:
        self.canvas.setFont(font, size)
        for line in wrap_text(s, font=font, size=size, max_width=CONTENT_WIDTH):
            self.canvas.drawString(LEFT_MARGIN, self.y, line)
            self.y -= LINE_HEIGHT

    def gap(self, height: float = LINE_HEIGHT) -> None:
        self.y -= height


def _draw_body(canvas: Canvas, *, invoice: Invoice, seller: Seller) -> None:
    cursor = _Cursor(canvas=canvas, y=_y_from_top(BODY_TOP))

    cursor.text(f"Rechnung Nr. {invoice.invoice_number}", font=FONT_BOLD, size=11)
    cursor.gap(LINE_HEIGHT * 1.5)

    totals = compute_totals(invoice)
    _draw_line_items_table(cursor, invoice, totals)
    cursor.gap()
    _draw_totals(cursor, totals, invoice.currency)
    cursor.gap(LINE_HEIGHT * 1.5)

    due_clause = f" bis zum {format_date_de(invoice.due_date)}" if invoice.due_date else ""
    cursor.text(
        f"Bitte überweisen Sie den Rechnungsbetrag{due_clause} unter Angabe der Rechnungsnummer auf folgendes Konto:"
    )
    cursor.gap(LINE_HEIGHT * 0.5)
    cursor.text(f"{seller.bank_details.bank_name}, IBAN {seller.bank_details.iban}, BIC {seller.bank_details.bic}")

    if invoice.notes:
        cursor.gap()
        cursor.text(invoice.notes)

    cursor.gap(LINE_HEIGHT * 1.5)
    cursor.text("Mit freundlichen Grüßen")
    cursor.gap(LINE_HEIGHT * 2)
    cursor.text(seller.name)


def _draw_line_items_table(cursor: _Cursor, invoice: Invoice, totals: InvoiceTotals) -> None:
    canvas = cursor.canvas

    canvas.setFont(FONT_BOLD, 8)
    canvas.drawString(COL_DESC_X, cursor.y, "Beschreibung")
    canvas.drawRightString(COL_QTY_X, cursor.y, "Menge")
    canvas.drawRightString(COL_PRICE_X, cursor.y, "Einzelpreis")
    canvas.drawRightString(COL_VAT_X, cursor.y, "USt.")
    canvas.drawRightString(COL_AMOUNT_X, cursor.y, "Betrag")
    cursor.y -= 2 * mm
    canvas.setLineWidth(0.4)
    canvas.line(LEFT_MARGIN, cursor.y, CONTENT_RIGHT, cursor.y)
    cursor.y -= LINE_HEIGHT

    canvas.setFont(FONT_REGULAR, BODY_FONT_SIZE)
    for line in totals.line_amounts:
        item = line.item
        quantity_text = f"{format_decimal_de(item.quantity)} {format_unit_de(item.unit)}"
        quantity_width = stringWidth(quantity_text, FONT_REGULAR, BODY_FONT_SIZE)
        desc_max_width = COL_QTY_X - COL_DESC_X - quantity_width - DESC_COL_GAP
        desc_lines = wrap_text(item.description, font=FONT_REGULAR, size=BODY_FONT_SIZE, max_width=desc_max_width)

        canvas.drawString(COL_DESC_X, cursor.y, desc_lines[0])
        canvas.drawRightString(COL_QTY_X, cursor.y, quantity_text)
        canvas.drawRightString(COL_PRICE_X, cursor.y, format_amount(item.unit_price_net, invoice.currency))
        canvas.drawRightString(COL_VAT_X, cursor.y, format_percent(item.vat_rate))
        canvas.drawRightString(COL_AMOUNT_X, cursor.y, format_amount(line.net_amount, invoice.currency))
        cursor.y -= LINE_HEIGHT

        for desc_line in desc_lines[1:]:
            canvas.drawString(COL_DESC_X, cursor.y, desc_line)
            cursor.y -= LINE_HEIGHT

    canvas.line(LEFT_MARGIN, cursor.y + 2 * mm, CONTENT_RIGHT, cursor.y + 2 * mm)


def _draw_totals(cursor: _Cursor, totals: InvoiceTotals, currency: str) -> None:
    _totals_row(cursor, "Nettosumme", totals.net_total, currency, font=FONT_REGULAR)
    for group in totals.vat_groups:
        label = f"zzgl. {format_percent(group.rate)} USt. auf {format_amount(group.net_amount, currency)}"
        _totals_row(cursor, label, group.vat_amount, currency, font=FONT_REGULAR)
    _totals_row(cursor, "Gesamtbetrag", totals.gross_total, currency, font=FONT_BOLD)


def _totals_row(cursor: _Cursor, label: str, amount: Decimal, currency: str, *, font: str) -> None:
    cursor.canvas.setFont(font, BODY_FONT_SIZE)
    cursor.canvas.drawString(COL_DESC_X, cursor.y, label)
    cursor.canvas.drawRightString(COL_AMOUNT_X, cursor.y, format_amount(amount, currency))
    cursor.y -= LINE_HEIGHT
