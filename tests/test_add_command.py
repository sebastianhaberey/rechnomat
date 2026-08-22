from datetime import date
from pathlib import Path

import pytest
import yaml

from rechnomat.command.add import AddCommand
from rechnomat.command.init import InitCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def _setup_project(context: Context) -> None:
    InitCommand().run(context)


def _invoice_customer(path: Path) -> str:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["customer"]


def _invoice_issue_date(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))["issue_date"]


def test_add_invoice_copies_bundled_example_when_no_invoices_exist(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "invoices" / "DE000001.yml").unlink()

    AddCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000001.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_copies_highest_invoice_overall_for_new_customer(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "customers" / "other-gmbh.yml").write_text(
        (tmp_path / "customers" / "meier-gmbh.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )

    AddCommand(customer_name="other-gmbh").run(context)

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

    AddCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000003.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_preserves_yaml_comments(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    AddCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert "# references a Customer file by its filename stem" in target.read_text(encoding="utf-8")


def test_add_invoice_raises_when_customer_file_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    with pytest.raises(RuntimeError, match="Customer file not found"):
        AddCommand(customer_name="unknown-gmbh").run(context)


def test_add_invoice_without_customer_name_copies_highest_invoice_overall(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)

    AddCommand().run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert target.exists()
    # customer is left as-is, since none was specified to switch to
    assert _invoice_customer(target) == "meier-gmbh"


def test_add_invoice_uses_current_date_instead_of_copied_one(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    original = tmp_path / "invoices" / "DE000001.yml"
    original.write_text(
        original.read_text(encoding="utf-8").replace("issue_date: 2026-08-15", "issue_date: 2000-01-01"),
        encoding="utf-8",
    )

    AddCommand(customer_name="meier-gmbh").run(context)

    target = tmp_path / "invoices" / "DE000002.yml"
    assert _invoice_issue_date(target) == date.today()
    # original invoice must be untouched
    assert _invoice_issue_date(original) == date(2000, 1, 1)


def test_add_invoice_raises_when_source_has_no_issue_date_field(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    original = tmp_path / "invoices" / "DE000001.yml"
    issue_date_line = "issue_date: 2026-08-15  # invoice issue date (EN 16931 BT-2)\n"
    original.write_text(
        original.read_text(encoding="utf-8").replace(issue_date_line, ""),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="has no 'issue_date' field"):
        AddCommand(customer_name="meier-gmbh").run(context)


def test_add_invoice_without_customer_name_copies_bundled_example_when_no_invoices_exist(
    tmp_path, monkeypatch, context
):
    monkeypatch.chdir(tmp_path)
    _setup_project(context)
    (tmp_path / "invoices" / "DE000001.yml").unlink()

    AddCommand().run(context)

    target = tmp_path / "invoices" / "DE000001.yml"
    assert target.exists()
    assert _invoice_customer(target) == "meier-gmbh"
