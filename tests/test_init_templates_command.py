from pathlib import Path

import pytest

from rechnomat.command.init_templates import RESOURCES_TEMPLATES_DIR, InitTemplatesCommand
from rechnomat.model import Context, Paths


@pytest.fixture
def context(tmp_path) -> Context:
    return Context(debug=False, rechnomat_executable=Path("rechnomat"), paths=Paths(root=tmp_path, output_dir=tmp_path))


def test_init_templates_copies_bundled_templates(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    InitTemplatesCommand().run(context)

    target_dir = tmp_path / "templates"
    assert (target_dir / "template.html").read_text(encoding="utf-8") == (
        RESOURCES_TEMPLATES_DIR / "template.html"
    ).read_text(encoding="utf-8")
    assert (target_dir / "template.css").exists()
    assert (target_dir / "fonts").is_dir()


def test_init_templates_replaces_existing_directory(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    target_dir = tmp_path / "templates"
    target_dir.mkdir()
    (target_dir / "stale.txt").write_text("old", encoding="utf-8")

    InitTemplatesCommand().run(context)

    assert not (target_dir / "stale.txt").exists()
    assert (target_dir / "template.html").exists()


def test_init_templates_creates_directory_when_missing(tmp_path, monkeypatch, context):
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "templates").exists()

    InitTemplatesCommand().run(context)

    assert (tmp_path / "templates").is_dir()
