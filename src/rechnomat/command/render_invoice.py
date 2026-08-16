from rechnomat import ui
from rechnomat.invoice_numbering import find_highest_invoice_number
from rechnomat.invoice_pdf import render_invoice_pdf
from rechnomat.model import Context, Customer, Invoice, Seller
from rechnomat.yaml_io import load_model


class RenderInvoiceCommand:
    def __init__(self, *, invoice_number: str | None = None) -> None:
        super().__init__()
        self.invoice_number = invoice_number

    def run(self, context: Context) -> None:
        invoices_dir = context.paths.invoices_dir

        invoice_number = self.invoice_number or find_highest_invoice_number(invoices_dir)
        if invoice_number is None:
            raise RuntimeError(f"No invoices found in: {invoices_dir}")

        invoice_file = context.paths.invoice_file(invoice_number)
        if not invoice_file.exists():
            raise RuntimeError(f"Invoice file not found: {invoice_file}")
        invoice = load_model(invoice_file, Invoice)

        customer_file = context.paths.customer_file(invoice.customer)
        if not customer_file.exists():
            raise RuntimeError(f"Customer file not found: {customer_file}")
        customer = load_model(customer_file, Customer)

        seller_file = context.paths.seller_file
        if not seller_file.exists():
            raise RuntimeError(f"Seller file not found: {seller_file}")
        seller = load_model(seller_file, Seller)

        templates_dir = context.paths.templates_dir
        if not templates_dir.exists():
            raise RuntimeError(f"Templates directory not found: {templates_dir}")

        target_file = context.paths.output_dir / f"{invoice_number}.pdf"
        render_invoice_pdf(
            invoice=invoice,
            invoice_number=invoice_number,
            customer=customer,
            seller=seller,
            output_path=target_file,
            templates_dir=templates_dir,
        )

        ui.success("Rendered invoice PDF", str(target_file))
