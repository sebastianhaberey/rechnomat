from pathlib import Path

import pytest

from rechnomat.command.init import RESOURCES_DIR, InitCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def test_init_copies_all_bundled_resources(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    InitCommand().run(context)

    assert (tmp_path / "customers" / "meier-gmbh.yml").read_text(encoding="utf-8") == (
        RESOURCES_DIR / "customers" / "meier-gmbh.yml"
    ).read_text(encoding="utf-8")
    assert (tmp_path / "invoices").is_dir()
    assert (tmp_path / "seller" / "seller.yml").exists()
    assert (tmp_path / "templates" / "de" / "template.html").exists()
    assert (tmp_path / "templates" / "de" / "fonts").is_dir()
    assert (tmp_path / "backgrounds" / "letterhead.pdf").read_bytes() == (
        RESOURCES_DIR / "backgrounds" / "letterhead.pdf"
    ).read_bytes()
    assert (tmp_path / "output").is_dir()


def test_init_leaves_existing_directories_untouched(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    customers_dir = tmp_path / "customers"
    customers_dir.mkdir()
    existing = customers_dir / "do-not-touch.yml"
    existing.write_text('name: "do not touch"\n', encoding="utf-8")

    InitCommand().run(context)

    assert existing.read_text(encoding="utf-8") == 'name: "do not touch"\n'
    assert not (customers_dir / "meier-gmbh.yml").exists()


def test_init_fills_in_missing_directories_alongside_existing_ones(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "customers").mkdir()

    InitCommand().run(context)

    assert (tmp_path / "invoices").is_dir()
    assert (tmp_path / "seller" / "seller.yml").exists()
    assert (tmp_path / "templates" / "de" / "template.html").exists()


def test_init_with_overwrite_replaces_existing_directories(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    customers_dir = tmp_path / "customers"
    customers_dir.mkdir()
    existing = customers_dir / "do-not-touch.yml"
    existing.write_text('name: "do not touch"\n', encoding="utf-8")

    InitCommand(overwrite=True).run(context)

    assert not existing.exists()
    assert (customers_dir / "meier-gmbh.yml").exists()


def test_init_leaves_existing_output_directory_untouched_even_with_overwrite(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    existing = output_dir / "DE000001.pdf"
    existing.write_bytes(b"%PDF-fake")

    InitCommand(overwrite=True).run(context)

    assert existing.read_bytes() == b"%PDF-fake"
