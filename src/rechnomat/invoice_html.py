import base64
import re
from pathlib import Path

import jinja2

from rechnomat.formatting import format_amount, format_date_de, format_decimal_de, format_percent, format_unit_de
from rechnomat.invoice_calc import compute_totals
from rechnomat.letter_address import build_address_lines, build_return_address_line
from rechnomat.model import Customer, Invoice, Seller

_FONT_URL_RE = re.compile(r'url\("(fonts/[^"]+)"\)')


def render_invoice_html(*, invoice: Invoice, customer: Customer, seller: Seller, templates_dir: Path) -> str:
    """
    Render `invoice` as a fully self-contained HTML string (CSS inlined, fonts embedded as base64
    data URIs) using the template.html + template.css found in `templates_dir`. Does no browser
    rendering - see invoice_pdf.render_invoice_pdf for the Playwright/PDF step.
    """
    context = _build_context(invoice=invoice, customer=customer, seller=seller)
    context["inline_css"] = _read_css_with_embedded_fonts(templates_dir)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    return env.get_template("template.html").render(**context)


def _build_context(*, invoice: Invoice, customer: Customer, seller: Seller) -> dict:
    totals = compute_totals(invoice)
    return {
        "invoice": invoice,
        "return_address_line": build_return_address_line(seller),
        "address_lines": build_address_lines(customer),
        "issue_date_text": format_date_de(invoice.issue_date),
        "due_date_text": format_date_de(invoice.due_date) if invoice.due_date else None,
        "line_rows": [
            {
                "description": line.item.description,
                "quantity_text": f"{format_decimal_de(line.item.quantity)} {format_unit_de(line.item.unit)}",
                "unit_price_text": format_amount(line.item.unit_price_net, invoice.currency),
                "vat_rate_text": format_percent(line.item.vat_rate),
                "amount_text": format_amount(line.net_amount, invoice.currency),
            }
            for line in totals.line_amounts
        ],
        "net_total_text": format_amount(totals.net_total, invoice.currency),
        "vat_group_rows": [
            {
                "label": (
                    f"zzgl. {format_percent(group.rate)} USt. auf {format_amount(group.net_amount, invoice.currency)}"
                ),
                "amount_text": format_amount(group.vat_amount, invoice.currency),
            }
            for group in totals.vat_groups
        ],
        "gross_total_text": format_amount(totals.gross_total, invoice.currency),
        "notes": invoice.notes,
        "bank_details": seller.bank_details,
    }


def _read_css_with_embedded_fonts(templates_dir) -> str:
    css_text = (templates_dir / "template.css").read_text(encoding="utf-8")

    def _inline(match: re.Match) -> str:
        font_bytes = (templates_dir / match.group(1)).read_bytes()
        b64 = base64.b64encode(font_bytes).decode("ascii")
        return f'url("data:font/ttf;base64,{b64}")'

    return _FONT_URL_RE.sub(_inline, css_text)
