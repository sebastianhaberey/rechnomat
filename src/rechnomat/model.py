from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field, computed_field, model_validator


@dataclass(frozen=True, slots=True)
class Paths:
    root: Path
    output_dir: Path

    @property
    def config_file(self) -> Path:
        return self.root / "rechnomat.toml"

    @property
    def customers_dir(self) -> Path:
        return self.root / "customers"

    @property
    def seller_dir(self) -> Path:
        return self.root / "seller"

    @property
    def seller_file(self) -> Path:
        return self.seller_dir / "seller.yml"

    @property
    def invoices_dir(self) -> Path:
        return self.root / "invoices"

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    @property
    def backgrounds_dir(self) -> Path:
        return self.root / "backgrounds"

    def template_dir(self, template_name: str) -> Path:
        return self.templates_dir / template_name

    def background_file(self, background_name: str) -> Path:
        return self.backgrounds_dir / background_name

    def customer_file(self, customer_name: str) -> Path:
        return self.customers_dir / f"{customer_name}.yml"

    def invoice_file(self, invoice_number: str) -> Path:
        return self.invoices_dir / f"{invoice_number}.yml"


@dataclass(slots=True)
class Context:
    debug: bool
    rechnomat_executable: Path
    paths: Paths


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    total: float | None = None
    current: float | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class Config:
    foo: str
    bar: str


class Address(BaseModel):
    street: str = Field(description="street and house number (EN 16931 BT-35/BT-50)")
    postcode: str = Field(description="postal code (EN 16931 BT-38/BT-53)")
    city: str = Field(description="city (EN 16931 BT-37/BT-52)")
    country_code: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2 (EN 16931 BT-40/BT-55)")


class Contact(BaseModel):
    name: str = Field(description="contact person (EN 16931 BT-41/BT-56)")
    email: str = Field(description="contact email address (EN 16931 BT-43/BT-58)")
    phone: str = Field(description="contact phone number (EN 16931 BT-42/BT-57)")


class Customer(BaseModel):
    name: str = Field(description="customer's legal/company name (EN 16931 BT-44)")
    legal_form: str | None = Field(default=None, description='e.g. "GmbH"; leave empty if already part of name')
    address: Address
    vat_id: str | None = Field(default=None, description="Ust-IdNr. (EN 16931 BT-48)")
    contact: Contact
    invoice_email: str = Field(
        description="invoice recipient address, e.g. an accounts-payable mailbox (EN 16931 BT-49)"
    )


class BankDetails(BaseModel):
    account_owner: str = Field(description="name on the bank account (EN 16931 BT-85)")
    iban: str = Field(description="IBAN (EN 16931 BT-84)")
    bic: str = Field(description="BIC (EN 16931 BT-86)")
    bank_name: str = Field(description="name of the bank")


class Seller(BaseModel):
    name: str = Field(description="seller's legal/company name (EN 16931 BT-27)")
    legal_form: str | None = Field(default=None, description='e.g. "GmbH"; leave empty if already part of name')
    address: Address
    vat_id: str | None = Field(default=None, description="Ust-IdNr. (EN 16931 BT-31)")
    tax_number: str | None = Field(default=None, description="Steuernummer (EN 16931 BT-32)")
    trade_register: str | None = Field(
        default=None, description='e.g. "Amtsgericht München, HRB 123456" (EN 16931 BT-30)'
    )
    contact: Contact
    invoice_email: str = Field(description="dedicated invoicing address, e.g. rechnungen@company.de (EN 16931 BT-34)")
    bank_details: BankDetails

    @model_validator(mode="after")
    def _check_tax_identification(self) -> Seller:
        # a seller must have a VAT identifier and/or a tax registration identifier (EN 16931 BR-CO-26)
        if not self.vat_id and not self.tax_number:
            raise ValueError("seller must have at least one of vat_id or tax_number")
        return self


class LineItem(BaseModel):
    description: str = Field(description="line item description (EN 16931 BT-153)")
    quantity: Decimal = Field(description="quantity (EN 16931 BT-129)")
    unit: str = Field(description='UN/ECE Recommendation 20 unit code, e.g. "HUR", "EA" (EN 16931 BT-130)')
    unit_price_net: Decimal = Field(description="net unit price (EN 16931 BT-146)")
    vat_rate: Decimal = Field(description="percent (EN 16931 BT-152)")

    @model_validator(mode="after")
    def _check_standard_vat_rate(self) -> LineItem:
        # only standard-rate VAT (category "S") is supported; zero/exempt/reverse-charge rates
        # need a legal exemption reason and category code we don't yet model (EN 16931 BG-23)
        if self.vat_rate <= 0:
            raise ValueError("vat_rate must be positive; zero/exempt VAT rates are not supported")
        return self


class Layout(BaseModel):
    template: str = Field(default="de", description="selects the template directory under templates/, e.g. 'de'")
    render_bank_details: bool = Field(default=True, description="show the seller's bank details on the invoice")
    render_notes: bool = Field(default=True, description="show the notes field on the invoice")
    render_return_address_line: bool = Field(
        default=True,
        description="show the small return-address line above the recipient address, for window envelopes",
    )
    background: str | None = Field(
        default=None, description="file under backgrounds/ merged behind the content, e.g. 'letterhead.pdf'"
    )


class Invoice(BaseModel):
    customer: str = Field(description="references a Customer file by its filename stem")
    layout: Layout = Field(default_factory=Layout)
    issue_date: date = Field(description="invoice issue date (EN 16931 BT-2)")
    payment_terms_days: int | None = Field(default=None, description="days from issue_date until due_date")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 (EN 16931 BT-5)")
    buyer_reference: str | None = Field(
        default=None, description="reference assigned by the buyer for internal routing (EN 16931 BT-10)"
    )
    line_items: list[LineItem] = Field(description="invoice line items (EN 16931 BG-25)")
    notes: str | None = Field(default=None, description="free-text note (EN 16931 BT-22)")

    @computed_field(description="invoice due date (EN 16931 BT-9)")
    @property
    def due_date(self) -> date | None:
        if self.payment_terms_days is None:
            return None
        return self.issue_date + timedelta(days=self.payment_terms_days)
