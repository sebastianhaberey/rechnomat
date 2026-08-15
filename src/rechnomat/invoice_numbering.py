import re
from pathlib import Path

_FILENAME_PATTERN = re.compile(r"^(\d+)\.yml$")
_DEFAULT_DIGIT_WIDTH = 8


def next_invoice_number(invoices_dir: Path) -> str:
    """
    Find the highest invoice number among `*.yml` files in `invoices_dir` whose filename is purely
    digits, and return the next number as a string, zero-padded to the same digit width. Falls back to
    "1", zero-padded to a default width, if no numbered invoice files exist yet.
    """
    highest_value: int | None = None
    highest_width = _DEFAULT_DIGIT_WIDTH

    if invoices_dir.exists():
        for path in invoices_dir.iterdir():
            match = _FILENAME_PATTERN.match(path.name)
            if not match:
                continue
            digits = match.group(1)
            value = int(digits)
            if highest_value is None or value > highest_value:
                highest_value = value
                highest_width = len(digits)

    next_value = 1 if highest_value is None else highest_value + 1
    return str(next_value).zfill(highest_width)
