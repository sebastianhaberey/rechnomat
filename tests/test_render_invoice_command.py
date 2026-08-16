import shutil
from pathlib import Path

import pytest

from rechnomat.command.init import InitCommand
from rechnomat.command.render_invoice import RenderInvoiceCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path, output_dir=tmp_path))


def _setup_project(context: Context) -> None:
    InitCommand().run(context)


def test_render_invoice_writes_pdf_for_explicit_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    RenderInvoiceCommand(invoice_number="DE000001").run(context)

    target = tmp_path / "DE000001.pdf"
    assert target.exists()
    assert target.read_bytes().startswith(b"%PDF-")


def test_render_invoice_defaults_to_highest_invoice_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    shutil.copy(tmp_path / "invoices" / "DE000001.yml", tmp_path / "invoices" / "DE000002.yml")

    RenderInvoiceCommand().run(context)

    assert (tmp_path / "DE000002.pdf").exists()
    assert not (tmp_path / "DE000001.pdf").exists()


def test_render_invoice_raises_when_no_invoices_exist(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    shutil.rmtree(tmp_path / "invoices")

    with pytest.raises(RuntimeError, match="No invoices found"):
        RenderInvoiceCommand().run(context)


def test_render_invoice_raises_for_unknown_invoice_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    with pytest.raises(RuntimeError, match="Invoice file not found"):
        RenderInvoiceCommand(invoice_number="00099999").run(context)


def test_render_invoice_raises_when_customer_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "customers" / "meier-gmbh.yml").unlink()

    with pytest.raises(RuntimeError, match="Customer file not found"):
        RenderInvoiceCommand(invoice_number="DE000001").run(context)


def test_render_invoice_raises_when_seller_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "seller" / "seller.yml").unlink()

    with pytest.raises(RuntimeError, match="Seller file not found"):
        RenderInvoiceCommand(invoice_number="DE000001").run(context)


def test_render_invoice_uses_renamed_file_as_source_of_truth_for_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "invoices" / "DE000001.yml").rename(tmp_path / "invoices" / "DE000009.yml")

    RenderInvoiceCommand(invoice_number="DE000009").run(context)

    assert (tmp_path / "DE000009.pdf").exists()
