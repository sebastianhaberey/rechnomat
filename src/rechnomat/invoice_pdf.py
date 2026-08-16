from io import BytesIO
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

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

    with sync_playwright() as playwright:
        # page.pdf() only works in headless mode.
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html)
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
        finally:
            browser.close()

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
