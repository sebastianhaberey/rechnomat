import re
from collections.abc import Callable
from pathlib import Path

_FILENAME_PATTERN = re.compile(r"^(\D*)(\d+)\.yml$")


def find_highest_invoice_number(invoices_dir: Path) -> str | None:
    """
    Find the highest invoice number among `*.yml` files in `invoices_dir` whose filename ends in a run
    of digits, and return it as written (preserving any non-digit prefix and zero-padding). Returns
    None if no numbered invoice files exist.
    """
    return find_highest_matching_invoice_number(invoices_dir, predicate=lambda _path: True)


def find_highest_matching_invoice_number(invoices_dir: Path, predicate: Callable[[Path], bool]) -> str | None:
    """
    Like `find_highest_invoice_number`, but only considers files for which `predicate` returns True.
    """
    highest_value: int | None = None
    highest_prefix = ""
    highest_digits: str | None = None

    if invoices_dir.exists():
        for path in invoices_dir.iterdir():
            match = _FILENAME_PATTERN.match(path.name)
            if not match or not predicate(path):
                continue
            prefix, digits = match.group(1), match.group(2)
            value = int(digits)
            if highest_value is None or value > highest_value:
                highest_value = value
                highest_prefix = prefix
                highest_digits = digits

    if highest_digits is None:
        return None
    return highest_prefix + highest_digits


def increment_invoice_number(invoice_number: str) -> str:
    """
    Increment the trailing run of digits in `invoice_number` by one, preserving any non-digit prefix
    and the original zero-padding width (unless the increment itself needs more digits).
    """
    match = re.match(r"^(\D*)(\d+)$", invoice_number)
    if not match:
        raise ValueError(f"Invoice number has no trailing digits: {invoice_number!r}")
    prefix, digits = match.group(1), match.group(2)
    incremented = str(int(digits) + 1).zfill(len(digits))
    return prefix + incremented
