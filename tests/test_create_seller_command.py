from pathlib import Path

import pytest

from rechnomat.command.create_seller import CreateSellerCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path))


def test_create_seller_writes_file_with_expected_content(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    CreateSellerCommand().run(context)

    content = (tmp_path / "seller" / "seller.yml").read_text(encoding="utf-8")
    assert content.startswith('name: ""\n')
    assert 'legal_form: ""' in content


def test_create_seller_creates_seller_directory_if_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "seller").exists()
    CreateSellerCommand().run(context)
    assert (tmp_path / "seller").is_dir()


def test_create_seller_refuses_to_overwrite_existing_file(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    seller_dir = tmp_path / "seller"
    seller_dir.mkdir()
    existing = seller_dir / "seller.yml"
    existing.write_text('name: "do not touch"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="already exists"):
        CreateSellerCommand().run(context)

    assert existing.read_text(encoding="utf-8") == 'name: "do not touch"\n'
