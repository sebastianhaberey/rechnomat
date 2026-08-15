from rechnomat import ui
from rechnomat.model import Config, Context
from rechnomat.theme import StyleId, theme

STYLES = theme().styles


class InfoCommand:
    def __init__(self) -> None:
        super().__init__()

    def run(self, context: Context) -> None:
        rows = [
            ("rechnomat executable", context.rechnomat_executable),
            ("seller dir", context.paths.seller_dir),
            ("customers dir", context.paths.customers_dir),
            ("invoices dir", context.paths.invoices_dir),
        ]
        ui.header("Configuration", first=True)
        ui.table(
            rows,
            column_colors=(STYLES[StyleId.PRIMARY], None),
        )
