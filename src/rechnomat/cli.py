import logging
from pathlib import Path

import cloup
from click import help_option, pass_obj, version_option
from cloup import HelpFormatter, HelpTheme, Section, argument, group, option, pass_context

from rechnomat.command.add_invoice import AddInvoiceCommand
from rechnomat.command.info import InfoCommand
from rechnomat.command.init import InitCommand
from rechnomat.command.render_invoice import RenderInvoiceCommand
from rechnomat.model import Context, Paths
from rechnomat.theme import StyleId, theme

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


@group(help="Rechnomat - create invoices compliant with German E-Rechnung laws", context_settings=CONTEXT_SETTINGS)
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

    paths = Paths(root=Path.cwd(), output_dir=Path.cwd())
    rechnomat_executable = ctx.obj.pop("rechnomat_executable", None)

    ctx.obj["context"] = Context(
        debug=debug,
        rechnomat_executable=rechnomat_executable,
        paths=paths,
    )


@cli.command(section=SECTION_MAIN)
@option(
    "-o",
    "--overwrite",
    is_flag=True,
    help="Replace existing directories instead of skipping them",
)
@help_option(help="Show this message")
@pass_obj
def init(obj, overwrite):
    """
    Copy the bundled example customers, invoices, seller and templates into the current directory
    """
    command = InitCommand(overwrite=overwrite)
    command.run(obj["context"])


@cli.command(section=SECTION_MAIN, name="add-invoice")
@argument(
    "customer-name",
    required=False,
    help="Customer to create the invoice for, references a Customer file by its filename stem (defaults to "
    "whichever customer is on the most recent invoice)",
)
@help_option(help="Show this message")
@pass_obj
def add_invoice(obj, customer_name):
    """
    Add a new invoice, copying the customer's most recent invoice, or the most recent invoice
    overall, or the bundled example invoice - whichever is found first
    """
    command = AddInvoiceCommand(customer_name=customer_name)
    command.run(obj["context"])


@cli.command(section=SECTION_MAIN, name="render-invoice")
@argument(
    "invoice-number",
    required=False,
    help="Invoice number to render (defaults to the highest-numbered invoice in invoices/)",
)
@help_option(help="Show this message")
@pass_obj
def render_invoice(obj, invoice_number):
    """
    Render an invoice as a PDF
    """
    command = RenderInvoiceCommand(invoice_number=invoice_number)
    command.run(obj["context"])


@cli.command(section=SECTION_UTILITY)
@help_option(help="Show this message")
@pass_obj
def info(obj):
    """
    Show current configuration, paths etc.
    """
    command = InfoCommand()
    command.run(obj["context"])
