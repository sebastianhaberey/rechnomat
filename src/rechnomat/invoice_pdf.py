from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

from rechnomat.invoice_html import render_invoice_html
from rechnomat.model import Customer, Invoice, Seller


def render_invoice_pdf(
    *,
    invoice: Invoice,
    invoice_number: str,
    customer: Customer,
    seller: Seller,
    output_path: Path,
    template_dir: Path,
    background_path: Path | None = None,
) -> None:
    """
    Render `invoice` as a DIN 5008 Form A letter PDF: address field, letter body with line items and
    totals. If `background_path` is given, its first page (e.g. a letterhead) is merged behind every
    content page via pypdf. No embedded EN 16931 XML yet - that is added in a later step.
    """
    html = render_invoice_html(
        invoice=invoice, invoice_number=invoice_number, customer=customer, seller=seller, template_dir=template_dir
    )

    # Page size and zero margin come from the `@page` rule in template.css.
    pdf_bytes = HTML(string=html).write_pdf()

    if background_path is not None:
        pdf_bytes = _merge_background(pdf_bytes, background_path)

    output_path.write_bytes(pdf_bytes)


def _merge_background(content_bytes: bytes, background_path: Path) -> bytes:
    """
    Overlay each page of `content_bytes` onto a copy of `background_path`'s first page, so the
    background (e.g. a letterhead) repeats behind every content page.
    """
    background_bytes = background_path.read_bytes()
    writer = PdfWriter()

    for content_page in PdfReader(BytesIO(content_bytes)).pages:
        background_page = PdfReader(BytesIO(background_bytes)).pages[0]
        merged_page = writer.add_page(background_page)
        merged_page.merge_page(content_page)

    merged_buffer = BytesIO()
    writer.write(merged_buffer)
    return merged_buffer.getvalue()
