from io import BytesIO
from pathlib import Path

from facturx import generate_from_binary
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
    Render `invoice` as a DIN 5008 Form A letter PDF/A-3b: address field, letter body with line
    items and totals. If `background_path` is given, its first page (e.g. a letterhead) is merged
    behind every content page via pypdf. No embedded EN 16931 XML yet - see embed_invoice_xml
    below for that step.
    """
    html = render_invoice_html(
        invoice=invoice, invoice_number=invoice_number, customer=customer, seller=seller, template_dir=template_dir
    )

    # Page size and zero margin come from the `@page` rule in template.css. pdf_variant="pdf/a-3b"
    # makes WeasyPrint itself emit a PDF/A-3b compliant file (sRGB OutputIntent, PDF/A XMP,
    # embedded fonts) - required before embed_invoice_xml can turn this into a ZUGFeRD container.
    pdf_bytes = HTML(string=html).write_pdf(pdf_variant="pdf/a-3b")

    if background_path is not None:
        pdf_bytes = _merge_background(pdf_bytes, background_path)

    output_path.write_bytes(pdf_bytes)


def _merge_background(content_bytes: bytes, background_path: Path) -> bytes:
    """
    Overlay `background_path`'s first page under each page of `content_bytes`, so the background
    (e.g. a letterhead) repeats behind every content page. Clones from the content PDF (not the
    background) and merges the background underneath, so the content PDF's PDF/A-3
    metadata/OutputIntent survive the merge.
    """
    background_bytes = background_path.read_bytes()
    writer = PdfWriter(clone_from=BytesIO(content_bytes))

    for page in writer.pages:
        background_page = PdfReader(BytesIO(background_bytes)).pages[0]
        page.merge_page(background_page, over=False)

    merged_buffer = BytesIO()
    writer.write(merged_buffer)
    return merged_buffer.getvalue()


def embed_invoice_xml(pdf_bytes: bytes, xml_bytes: bytes) -> bytes:
    """
    Embed `xml_bytes` (EN 16931 CII XML, see invoice_xml.build_invoice_xml) into `pdf_bytes` as a
    Factur-X/ZUGFeRD EN16931-level attachment, producing the final conformant PDF/A-3 container.
    `pdf_bytes` must already be PDF/A-3-compliant (see render_invoice_pdf's pdf_variant="pdf/a-3b").
    """
    return generate_from_binary(pdf_bytes, xml_bytes, flavor="factur-x", level="en16931", check_xsd=True)
