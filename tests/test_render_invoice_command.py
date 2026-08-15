from pathlib import Path

import pytest

from rechnomat.command.render_invoice import RenderInvoiceCommand
from rechnomat.model import Context, Paths

CUSTOMER_YAML = """\
name: "ACME GmbH"
address:
  street: "Musterstrasse 12"
  postcode: "10115"
  city: "Berlin"
  country_code: "DE"
contact:
  name: "Maria Mustermann"
  email: "maria@acme.example"
  phone: "+49 30 1234567"
payment_terms_days: 14
"""

SELLER_YAML = """\
name: "Musterfirma Max Mustermann"
address:
  street: "Beispielweg 5"
  postcode: "80331"
  city: "Muenchen"
  country_code: "DE"
vat_id: "DE987654321"
contact:
  name: "Max Mustermann"
  email: "max@musterfirma.example"
  phone: "+49 89 1234567"
bank_details:
  account_owner: "Musterfirma Max Mustermann"
  iban: "DE02120300000000202051"
  bic: "BYLADEM1001"
  bank_name: "Deutsche Kreditbank"
"""

INVOICE_YAML = """\
invoice_number: "{number}"
customer: "acme-gmbh"
issue_date: 2026-08-15
due_date: 2026-08-29
currency: "EUR"
line_items:
  - description: "Consulting services"
    quantity: "8"
    unit: "HUR"
    unit_price_net: "120.00"
    vat_rate: "19"
"""


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def _setup_project(cwd: Path, *, invoice_number: str = "00000001") -> None:
    (cwd / "customers").mkdir(parents=True, exist_ok=True)
    (cwd / "customers" / "acme-gmbh.yml").write_text(CUSTOMER_YAML, encoding="utf-8")

    (cwd / "seller").mkdir(parents=True, exist_ok=True)
    (cwd / "seller" / "seller.yml").write_text(SELLER_YAML, encoding="utf-8")

    (cwd / "invoices").mkdir(parents=True, exist_ok=True)
    (cwd / "invoices" / f"{invoice_number}.yml").write_text(
        INVOICE_YAML.format(number=invoice_number), encoding="utf-8"
    )


def test_render_invoice_writes_pdf_for_explicit_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)

    RenderInvoiceCommand(invoice_number="00000001").run(context)

    target = tmp_path / "invoices" / "00000001.pdf"
    assert target.exists()
    assert target.read_bytes().startswith(b"%PDF-")


def test_render_invoice_defaults_to_highest_invoice_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path, invoice_number="00000001")
    _setup_project(tmp_path, invoice_number="00000002")

    RenderInvoiceCommand().run(context)

    assert (tmp_path / "invoices" / "00000002.pdf").exists()
    assert not (tmp_path / "invoices" / "00000001.pdf").exists()


def test_render_invoice_raises_when_no_invoices_exist(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="No invoices found"):
        RenderInvoiceCommand().run(context)


def test_render_invoice_raises_for_unknown_invoice_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)

    with pytest.raises(RuntimeError, match="Invoice file not found"):
        RenderInvoiceCommand(invoice_number="00099999").run(context)


def test_render_invoice_raises_when_customer_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    (tmp_path / "customers" / "acme-gmbh.yml").unlink()

    with pytest.raises(RuntimeError, match="Customer file not found"):
        RenderInvoiceCommand(invoice_number="00000001").run(context)


def test_render_invoice_raises_when_seller_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    (tmp_path / "seller" / "seller.yml").unlink()

    with pytest.raises(RuntimeError, match="Seller file not found"):
        RenderInvoiceCommand(invoice_number="00000001").run(context)


def test_render_invoice_raises_when_file_name_does_not_match_invoice_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(tmp_path)
    (tmp_path / "invoices" / "00000001.yml").rename(tmp_path / "invoices" / "00000002.yml")

    with pytest.raises(RuntimeError, match="Invoice number mismatch"):
        RenderInvoiceCommand(invoice_number="00000002").run(context)
