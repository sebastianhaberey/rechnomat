from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Context:
    debug: bool
    rechnomat_executable: Path
    config_file: Path


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    total: float | None = None
    current: float | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class Config:
    foo: str
    bar: str
