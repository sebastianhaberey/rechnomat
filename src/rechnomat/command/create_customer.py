from rechnomat import ui
from rechnomat.model import Context, Customer
from rechnomat.scaffold import render_scaffold


class CreateCustomerCommand:
    def __init__(self, *, customer_name: str) -> None:
        super().__init__()
        self.customer_name = customer_name

    def run(self, context: Context) -> None:
        customers_dir = context.paths.customers_dir
        target_file = context.paths.customer_file(self.customer_name)

        if target_file.exists():
            raise RuntimeError(f"Customer file already exists: {target_file}")

        customers_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(render_scaffold(Customer, overrides={"name": self.customer_name}), encoding="utf-8")

        ui.success("Created customer file", str(target_file))
