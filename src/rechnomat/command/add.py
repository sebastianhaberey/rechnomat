import re
from pathlib import Path

import yaml

from rechnomat import ui
from rechnomat.command.init import RESOURCES_DIR
from rechnomat.invoice_numbering import (
    find_highest_invoice_number,
    find_highest_matching_invoice_number,
    increment_invoice_number,
)
from rechnomat.model import Context

EXAMPLE_INVOICES_DIR = RESOURCES_DIR / "invoices"

_CUSTOMER_FIELD_PATTERN = re.compile(r'^(customer:\s*)"[^"]*"', re.MULTILINE)


class AddCommand:
    def __init__(self, *, customer_name: str | None = None) -> None:
        super().__init__()
        self.customer_name = customer_name

    def run(self, context: Context) -> None:
        paths = context.paths

        if self.customer_name is not None:
            customer_file = paths.customer_file(self.customer_name)
            if not customer_file.exists():
                raise RuntimeError(f"Customer file not found: {customer_file}")

        invoices_dir = paths.invoices_dir
        customer_invoice_number = (
            find_highest_matching_invoice_number(invoices_dir, self._belongs_to_customer)
            if self.customer_name is not None
            else None
        )
        highest_invoice_number = find_highest_invoice_number(invoices_dir)

        if customer_invoice_number is not None:
            source_file = paths.invoice_file(customer_invoice_number)
            rewrite_customer = False
        elif highest_invoice_number is not None:
            source_file = paths.invoice_file(highest_invoice_number)
            rewrite_customer = self.customer_name is not None
        else:
            example_number = find_highest_invoice_number(EXAMPLE_INVOICES_DIR)
            if example_number is None:
                raise RuntimeError(f"No example invoice found in: {EXAMPLE_INVOICES_DIR}")
            source_file = EXAMPLE_INVOICES_DIR / f"{example_number}.yml"
            rewrite_customer = self.customer_name is not None

        if not source_file.exists():
            raise RuntimeError(f"Invoice file not found: {source_file}")

        new_invoice_number = (
            increment_invoice_number(highest_invoice_number) if highest_invoice_number is not None else source_file.stem
        )

        target_file = paths.invoice_file(new_invoice_number)

        content = source_file.read_text(encoding="utf-8")
        if rewrite_customer:
            content = self._with_customer(content)

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content, encoding="utf-8")

        ui.success("Added invoice", str(target_file))

    def _belongs_to_customer(self, invoice_file: Path) -> bool:
        data = yaml.safe_load(invoice_file.read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("customer") == self.customer_name

    def _with_customer(self, content: str) -> str:
        new_content, count = _CUSTOMER_FIELD_PATTERN.subn(rf'\1"{self.customer_name}"', content, count=1)
        if count == 0:
            raise RuntimeError("Source invoice file has no 'customer' field to replace")
        return new_content
