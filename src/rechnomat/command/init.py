import importlib.resources
import shutil

from rechnomat import ui
from rechnomat.model import Context

RESOURCES_DIR = importlib.resources.files("rechnomat") / "resources"


class InitCommand:
    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite

    def run(self, context: Context) -> None:
        paths = context.paths
        resources = (
            ("customers", paths.customers_dir),
            ("invoices", paths.invoices_dir),
            ("seller", paths.seller_dir),
            ("templates", paths.templates_dir),
        )

        for name, target_dir in resources:
            replaced = False

            if target_dir.exists():
                if not self.overwrite:
                    ui.warn("Skipped", f"{target_dir} (already exists)")
                    continue

                shutil.rmtree(target_dir)
                replaced = True

            shutil.copytree(RESOURCES_DIR / name, target_dir)
            ui.success("Replaced" if replaced else "Copied", str(target_dir))
