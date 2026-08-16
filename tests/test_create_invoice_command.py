from pathlib import Path

import pytest

from rechnomat.command.create_invoice import CreateInvoiceCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path, output_dir=tmp_path))


def _create_customer(cwd: Path, customer: str) -> None:
    customers_dir = cwd / "customers"
    customers_dir.mkdir(parents=True, exist_ok=True)
    (customers_dir / f"{customer}.yml").write_text('name: ""\n', encoding="utf-8")


def test_create_invoice_writes_first_invoice_with_default_width(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _create_customer(tmp_path, "acme-gmbh")

    CreateInvoiceCommand(customer="acme-gmbh").run(context)

    target = tmp_path / "invoices" / "00000001.yml"
    content = target.read_text(encoding="utf-8")
    assert content.startswith('customer: "acme-gmbh"')


def test_create_invoice_increments_highest_existing_number(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _create_customer(tmp_path, "acme-gmbh")
    invoices_dir = tmp_path / "invoices"
    invoices_dir.mkdir()
    (invoices_dir / "00000005.yml").touch()

    CreateInvoiceCommand(customer="acme-gmbh").run(context)

    assert (invoices_dir / "00000006.yml").exists()


def test_create_invoice_refuses_for_unknown_customer(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="Customer file not found"):
        CreateInvoiceCommand(customer="does-not-exist").run(context)

    assert not (tmp_path / "invoices").exists()
