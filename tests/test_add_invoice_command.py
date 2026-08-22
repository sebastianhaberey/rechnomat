from pathlib import Path

import pytest
import yaml

from rechnomat.command.add_invoice import AddInvoiceCommand
from rechnomat.command.init import InitCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def _setup_project(context: Context) -> None:
    InitCommand().run(context)


def _invoice_customer(path: Path) -> str:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["customer"]


def test_add_invoice_copies_bundled_example_when_no_invoices_exist(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "invoices" / "DE000001.yml").unlink()

    AddInvoiceCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000001.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_copies_highest_invoice_overall_for_new_customer(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "customers" / "other-gmbh.yml").write_text(
        (tmp_path / "customers" / "meier-gmbh.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )

    AddInvoiceCommand(customer_name="other-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert target.exists()
    assert _invoice_customer(target) == "other-gmbh"
    # original invoice for meier-gmbh must be untouched
    assert _invoice_customer(tmp_path / "invoices" / "DE000001.yml") == "meier-gmbh"


def test_add_invoice_copies_highest_invoice_for_same_customer(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "customers" / "other-gmbh.yml").write_text(
        (tmp_path / "customers" / "meier-gmbh.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    other_invoice = tmp_path / "invoices" / "DE000002.yml"
    other_invoice.write_text(
        (tmp_path / "invoices" / "DE000001.yml").read_text(encoding="utf-8").replace("meier-gmbh", "other-gmbh"),
        encoding="utf-8",
    )

    AddInvoiceCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000003.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_preserves_yaml_comments(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    AddInvoiceCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert "# references a Customer file by its filename stem" in target.read_text(encoding="utf-8")


def test_add_invoice_raises_when_customer_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    with pytest.raises(RuntimeError, match="Customer file not found"):
        AddInvoiceCommand(customer_name="unknown-gmbh").run(context)


def test_add_invoice_without_customer_name_copies_highest_invoice_overall(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    AddInvoiceCommand().run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert target.exists()
    # customer is left as-is, since none was specified to switch to
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_without_customer_name_copies_bundled_example_when_no_invoices_exist(
    tmp_path, monkeypatch, context
):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "invoices" / "DE000001.yml").unlink()

    AddInvoiceCommand().run(context)

    target = tmp_path / "invoices" / "DE000001.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"
