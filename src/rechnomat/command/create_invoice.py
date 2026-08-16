from rechnomat import ui
from rechnomat.invoice_numbering import next_invoice_number
from rechnomat.model import Context, Invoice
from rechnomat.scaffold import render_scaffold


class CreateInvoiceCommand:
    def __init__(self, *, customer: str) -> None:
        super().__init__()
        self.customer = customer

    def run(self, context: Context) -> None:
        customer_file = context.paths.customer_file(self.customer)
        if not customer_file.exists():
            raise RuntimeError(f"Customer file not found: {customer_file}")

        invoices_dir = context.paths.invoices_dir
        invoice_number = next_invoice_number(invoices_dir)

        invoices_dir.mkdir(parents=True, exist_ok=True)
        target_file = context.paths.invoice_file(invoice_number)
        target_file.write_text(
            render_scaffold(Invoice, overrides={"customer": self.customer}),
            encoding="utf-8",
        )

        ui.success("Created invoice file", str(target_file))
