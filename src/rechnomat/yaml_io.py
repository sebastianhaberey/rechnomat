from pathlib import Path

import yaml
from pydantic import BaseModel


def load_model[T: BaseModel](path: Path, model: type[T]) -> T:
    """
    Load a YAML file at `path` and parse it into `model`.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return model.model_validate(data)
