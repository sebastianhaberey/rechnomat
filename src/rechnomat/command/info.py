from rechnomat import ui
from rechnomat.model import Context
from rechnomat.theme import StyleId, theme

STYLES = theme().styles


class InfoCommand:
    def __init__(self) -> None:
        super().__init__()

    def run(self, context: Context) -> None:
        rows = [
            ("Executable", context.rechnomat_executable),
            ("Customers directory", context.paths.customers_dir),
            ("Invoices directory", context.paths.invoices_dir),
            ("Seller directory", context.paths.seller_dir),
            ("Templates directory", context.paths.templates_dir),
            ("Output directory", context.paths.output_dir),
        ]
        ui.header("Context", first=True)
        ui.table(
            rows,
            column_colors=(STYLES[StyleId.PRIMARY], None),
        )
