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
    highest = find_highest_invoice_number(invoices_dir)
    if highest is None:
        return str(1).zfill(_DEFAULT_DIGIT_WIDTH)
    return str(int(highest) + 1).zfill(len(highest))


def find_highest_invoice_number(invoices_dir: Path) -> str | None:
    """
    Find the highest invoice number among `*.yml` files in `invoices_dir` whose filename is purely
    digits, and return it as written (preserving zero-padding). Returns None if no numbered invoice
    files exist.
    """
    highest_value: int | None = None
    highest_digits: str | None = None

    if invoices_dir.exists():
        for path in invoices_dir.iterdir():
            match = _FILENAME_PATTERN.match(path.name)
            if not match:
                continue
            digits = match.group(1)
            value = int(digits)
            if highest_value is None or value > highest_value:
                highest_value = value
                highest_digits = digits

    return highest_digits
