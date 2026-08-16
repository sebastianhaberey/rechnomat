from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


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
    street: str
    postcode: str
    city: str
    country_code: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2, EN 16931 BT-55")


class Contact(BaseModel):
    name: str
    email: str
    phone: str


class Customer(BaseModel):
    name: str
    legal_form: str | None = None
    address: Address
    vat_id: str | None = Field(default=None, description="Ust-IdNr., EN 16931 BT-48")
    contact: Contact
    payment_terms_days: int
    notes: str | None = None


class BankDetails(BaseModel):
    account_owner: str
    iban: str = Field(description="EN 16931 BT-84")
    bic: str = Field(description="EN 16931 BT-86")
    bank_name: str


class Seller(BaseModel):
    name: str
    legal_form: str | None = None
    address: Address
    vat_id: str | None = Field(default=None, description="Ust-IdNr., EN 16931 BT-31")
    tax_number: str | None = Field(default=None, description="Steuernummer, EN 16931 BT-32")
    trade_register: str | None = Field(
        default=None, description='e.g. "Amtsgericht München, HRB 123456"; EN 16931 BT-30'
    )
    contact: Contact
    bank_details: BankDetails

    @model_validator(mode="after")
    def _check_tax_identification(self) -> Seller:
        # EN 16931 BR-CO-26: a seller must have a VAT identifier and/or a tax registration identifier.
        if not self.vat_id and not self.tax_number:
            raise ValueError("seller must have at least one of vat_id or tax_number")
        return self


class LineItem(BaseModel):
    description: str
    quantity: Decimal
    unit: str = Field(description='UN/ECE Recommendation 20 unit code, e.g. "HUR", "EA"')
    unit_price_net: Decimal
    vat_rate: Decimal = Field(description="percent")


class Invoice(BaseModel):
    customer: str = Field(description="references a Customer file by its filename stem")
    issue_date: date = Field(description="EN 16931 BT-2")
    due_date: date | None = None
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217, EN 16931 BT-5")
    buyer_reference: str | None = Field(default=None, description="EN 16931 BT-10")
    line_items: list[LineItem] = Field(description="EN 16931 BG-25")
    notes: str | None = Field(default=None, description="EN 16931 BT-22")
