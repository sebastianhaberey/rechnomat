import logging
from pathlib import Path

import cloup
from click import help_option, pass_obj, version_option
from cloup import HelpFormatter, HelpTheme, Section, argument, group, option, pass_context

from rechnomat.command.create_customer import CreateCustomerCommand
from rechnomat.command.create_invoice import CreateInvoiceCommand
from rechnomat.command.create_seller import CreateSellerCommand
from rechnomat.command.info import InfoCommand
from rechnomat.model import Context
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

    config_file = Path.cwd() / "rechnomat.toml"
    rechnomat_executable = ctx.obj.pop("rechnomat_executable", None)

    ctx.obj["context"] = Context(
        debug=debug,
        rechnomat_executable=rechnomat_executable,
        config_file=config_file,
    )

    # ctx.obj["config"] = config.load(config_file)


@cli.command(section=SECTION_MAIN)
@argument("customer-name", help="Name for the new customer file and its initial `name:` value")
@help_option(help="Show this message")
@pass_obj
def create_customer(obj, customer_name):
    """
    Create a new customer YAML file
    """
    command = CreateCustomerCommand(customer_name=customer_name)
    command.run(obj["context"])


@cli.command(section=SECTION_MAIN)
@help_option(help="Show this message")
@pass_obj
def create_seller(obj):
    """
    Create the seller YAML file
    """
    command = CreateSellerCommand()
    command.run(obj["context"])


@cli.command(section=SECTION_MAIN)
@argument("customer", help="Customer file this invoice is for (references customers/<customer>.yml)")
@help_option(help="Show this message")
@pass_obj
def create_invoice(obj, customer):
    """
    Create a new invoice YAML file
    """
    command = CreateInvoiceCommand(customer=customer)
    command.run(obj["context"])


@cli.command(section=SECTION_UTILITY)
@help_option(help="Show this message")
@pass_obj
def info(obj):
    """
    Show current configuration, paths etc.
    """
    command = InfoCommand(config=obj["config"])
    command.run(obj["context"])
