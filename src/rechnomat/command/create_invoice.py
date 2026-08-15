from pathlib import Path

from rechnomat import ui
from rechnomat.invoice_numbering import next_invoice_number
from rechnomat.model import Context, Invoice
from rechnomat.scaffold import render_scaffold


class CreateInvoiceCommand:
    def __init__(self, *, customer: str) -> None:
        super().__init__()
        self.customer = customer

    def run(self, context: Context) -> None:
        customer_file = Path.cwd() / "customers" / f"{self.customer}.yml"
        if not customer_file.exists():
            raise RuntimeError(f"Customer file not found: {customer_file}")

        invoices_dir = Path.cwd() / "invoices"
        invoice_number = next_invoice_number(invoices_dir)

        invoices_dir.mkdir(parents=True, exist_ok=True)
        target_file = invoices_dir / f"{invoice_number}.yml"
        target_file.write_text(
            render_scaffold(Invoice, overrides={"invoice_number": invoice_number, "customer": self.customer}),
            encoding="utf-8",
        )

        ui.success("Created invoice file", str(target_file))
