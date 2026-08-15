from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from rechnomat.model import Config


def load(path: Path) -> Config:
    """
    Load configuration from a TOML file.
    """
    try:
        with path.open("rb") as f:
            cfg = tomllib.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found at: {path}")
    return _parse(cfg)


def _parse(cfg: dict[str, Any]) -> Config:
    return Config(
        foo=cfg["foo"],
        bar=cfg["bar"],
    )
