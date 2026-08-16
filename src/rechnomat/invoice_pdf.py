from pathlib import Path

from playwright.sync_api import sync_playwright

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
) -> None:
    """
    Render `invoice` as a DIN 5008 Form A letter PDF: address field, letter body with line items and
    totals. No letterhead background or embedded EN 16931 XML yet - both are added in later steps.
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
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
        finally:
            browser.close()
