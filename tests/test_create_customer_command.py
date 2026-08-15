from pathlib import Path

import pytest

from rechnomat.command.create_customer import CreateCustomerCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def test_create_customer_writes_file_with_expected_content(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    CreateCustomerCommand(customer_name="acme-gmbh").run(context)

    content = (tmp_path / "customers" / "acme-gmbh.yml").read_text(encoding="utf-8")
    assert content.startswith('name: "acme-gmbh"\n')
    assert 'legal_form: ""' in content


def test_create_customer_creates_customers_directory_if_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "customers").exists()
    CreateCustomerCommand(customer_name="new-customer").run(context)
    assert (tmp_path / "customers").is_dir()


def test_create_customer_refuses_to_overwrite_existing_file(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    customers_dir = tmp_path / "customers"
    customers_dir.mkdir()
    existing = customers_dir / "acme-gmbh.yml"
    existing.write_text('name: "do not touch"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="already exists"):
        CreateCustomerCommand(customer_name="acme-gmbh").run(context)

    assert existing.read_text(encoding="utf-8") == 'name: "do not touch"\n'
