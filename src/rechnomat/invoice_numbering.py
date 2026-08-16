import re
from pathlib import Path

_FILENAME_PATTERN = re.compile(r"^(\D*)(\d+)\.yml$")


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
