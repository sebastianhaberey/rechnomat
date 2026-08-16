import importlib.resources
import shutil

from rechnomat import ui
from rechnomat.model import Context

RESOURCES_DIR = importlib.resources.files("rechnomat") / "resources"


class InitCommand:
    def run(self, context: Context) -> None:
        paths = context.paths
        resources = (
            ("customers", paths.customers_dir),
            ("invoices", paths.invoices_dir),
            ("seller", paths.seller_dir),
            ("templates", paths.templates_dir),
        )

        for name, target_dir in resources:
            if target_dir.exists():
                ui.warn("Skipped", f"{target_dir} (already exists)")
                continue

            shutil.copytree(RESOURCES_DIR / name, target_dir)
            ui.success("Copied", str(target_dir))
