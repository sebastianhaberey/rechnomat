import logging
import os
from pathlib import Path

import cloup
from click import Choice, help_option, pass_obj, version_option
from cloup import HelpFormatter, HelpTheme, Section, argument, group, option, pass_context

import rechnomat
from rechnomat.theme import theme, StyleId

logger = logging.getLogger(__name__)

STYLES = theme().styles_cloup

CONTEXT_SETTINGS = cloup.Context.settings(
    formatter_settings=HelpFormatter.settings(
        theme=HelpTheme(
            invoked_command=STYLES[StyleId.SECONDARY],
            heading=STYLES[StyleId.HEADER],
            col1=STYLES[StyleId.PRIMARY],
        ),
        width=120,
        max_width=120,  # default is too low (80), but too high will yield really long help text lines
    ),
)

SECTION_MAIN = Section("Main commands")
SECTION_UTILITY = Section("Utility commands")

# TODO SH find a better way to pass debug flag to exception handling
DEBUG_MODE: bool = False


@group(help="Rechnomat", context_settings=CONTEXT_SETTINGS)
@help_option(help="Show this page")
@version_option(prog_name="Rechnomat", help="Show version information", message="%(prog)s version %(version)s")
@option(
    "--debug",
    envvar="EASYBORG_DEBUG",
    is_flag=True,
    help="Enable debug mode",
)
@pass_context
def cli(
        ctx: cloup.Context,
        debug: bool,
) -> None:
    # first, set DEBUG_MODE flag to enable stacktraces
    global DEBUG_MODE
    DEBUG_MODE = debug

    ctx.ensure_object(dict)

    rechnomat_executable = ctx.obj.pop("rechnomat_executable", None)  # move info from Click context to aplication context

    context = rechnomat.context.create(
        debug=debug,
    )
    ctx.obj["context"] = context
