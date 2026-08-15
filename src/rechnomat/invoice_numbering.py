import re
from pathlib import Path

_FILENAME_PATTERN = re.compile(r"^(\D*)(\d+)\.yml$")
_DEFAULT_DIGIT_WIDTH = 8


def next_invoice_number(invoices_dir: Path) -> str:
    """
    Find the highest invoice number among `*.yml` files in `invoices_dir` whose filename ends in a run
    of digits, and return the next number as a string: the digit portion incremented by one and
    zero-padded to the same width, with any non-digit prefix (e.g. "DE-") preserved unchanged. Falls
    back to "1", zero-padded to a default width, if no numbered invoice files exist yet.
    """
    prefix, digits = _find_highest_invoice_number_parts(invoices_dir)
    if digits is None:
        return str(1).zfill(_DEFAULT_DIGIT_WIDTH)
    return prefix + str(int(digits) + 1).zfill(len(digits))


def find_highest_invoice_number(invoices_dir: Path) -> str | None:
    """
    Find the highest invoice number among `*.yml` files in `invoices_dir` whose filename ends in a run
    of digits, and return it as written (preserving any non-digit prefix and zero-padding). Returns
    None if no numbered invoice files exist.
    """
    prefix, digits = _find_highest_invoice_number_parts(invoices_dir)
    if digits is None:
        return None
    return prefix + digits


def _find_highest_invoice_number_parts(invoices_dir: Path) -> tuple[str, str | None]:
    highest_value: int | None = None
    highest_prefix = ""
    highest_digits: str | None = None

    if invoices_dir.exists():
        for path in invoices_dir.iterdir():
            match = _FILENAME_PATTERN.match(path.name)
            if not match:
                continue
            prefix, digits = match.group(1), match.group(2)
            value = int(digits)
            if highest_value is None or value > highest_value:
                highest_value = value
                highest_prefix = prefix
                highest_digits = digits

    return highest_prefix, highest_digits
