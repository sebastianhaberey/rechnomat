from rechnomat import ui
from rechnomat.model import Context, Seller
from rechnomat.scaffold import render_scaffold


class CreateSellerCommand:
    def run(self, context: Context) -> None:
        seller_dir = context.paths.seller_dir
        target_file = context.paths.seller_file

        if target_file.exists():
            raise RuntimeError(f"Seller file already exists: {target_file}")

        seller_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(render_scaffold(Seller), encoding="utf-8")

        ui.success("Created seller file", str(target_file))
