from rechnomat import ui
from rechnomat.model import Config, Context
from rechnomat.theme import StyleId, theme

STYLES = theme().styles


class InfoCommand:
    def __init__(self, *, config: Config) -> None:
        super().__init__()
        self.config = config

    def run(self, context: Context) -> None:
        rows = [
            ("rechnomat executable", context.rechnomat_executable),
            ("foo", self.config.foo),
            ("bar", self.config.bar),
        ]
        ui.header("Configuration", first=True)
        ui.table(
            rows,
            column_colors=(STYLES[StyleId.PRIMARY], None),
        )
