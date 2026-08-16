import importlib.resources
import shutil

from rechnomat import ui
from rechnomat.model import Context

RESOURCES_TEMPLATES_DIR = importlib.resources.files("rechnomat") / "resources" / "templates"


class InitTemplatesCommand:
    def run(self, context: Context) -> None:
        target_dir = context.paths.templates_dir

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(RESOURCES_TEMPLATES_DIR, target_dir)

        ui.success("Initialized templates directory", str(target_dir))
