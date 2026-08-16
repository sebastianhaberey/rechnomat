from rechnomat import ui
from rechnomat.model import Context
from rechnomat.theme import StyleId, theme

STYLES = theme().styles


class InfoCommand:
    def __init__(self) -> None:
        super().__init__()

    def run(self, context: Context) -> None:
        rows = [
            ("executable", context.rechnomat_executable),
            ("customers dir", context.paths.customers_dir),
            ("invoices dir", context.paths.invoices_dir),
            ("seller dir", context.paths.seller_dir),
            ("templates dir", context.paths.templates_dir),
        ]
        ui.header("Configuration", first=True)
        ui.table(
            rows,
            column_colors=(STYLES[StyleId.PRIMARY], None),
        )
