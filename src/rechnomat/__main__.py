import sys
from pathlib import Path

import rechnomat.cli
from rechnomat import ui
from rechnomat.cli import cli


def main():
    args = sys.argv[1:]
    if render_newlines(args):
        ui.newline()
    try:
        rechnomat_executable = Path(sys.argv[0])
        cli.main(args, obj={"rechnomat_executable": rechnomat_executable})
    except Exception as e:
        if rechnomat.cli.DEBUG_MODE:
            ui.stacktrace("Error while running rechnomat")
        else:
            ui.exception(e)
    finally:
        if render_newlines(args):
            ui.newline()


def render_newlines(args: list[str]) -> bool:
    """Quick and dirty hack to evaluate if the two framing newlines should be rendered"""
    if "--headless" in args:
        return False  # don't output anything in headless mode to avoid system mails
    return True


if __name__ == "__main__":
    main()
