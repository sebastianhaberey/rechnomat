from pydantic import BaseModel

from rechnomat.yaml_io import load_model


class Widget(BaseModel):
    name: str
    count: int


def test_load_model_parses_yaml_into_model(tmp_path):
    path = tmp_path / "widget.yml"
    path.write_text("name: gadget\ncount: 3\n", encoding="utf-8")

    widget = load_model(path, Widget)

    assert widget == Widget(name="gadget", count=3)
