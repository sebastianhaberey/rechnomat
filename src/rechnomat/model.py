from dataclasses import dataclass


@dataclass(slots=True)
class Context:
    debug: bool

@dataclass(frozen=True, slots=True)
class ProgressEvent:
    total: float | None = None
    current: float | None = None
    message: str | None = None
