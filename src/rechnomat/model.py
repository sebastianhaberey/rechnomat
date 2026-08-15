from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


@dataclass(slots=True)
class Context:
    debug: bool
    rechnomat_executable: Path
    config_file: Path


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
    iban: str  # EN 16931 BT-84
    bic: str  # EN 16931 BT-86
    bank_name: str


class Seller(BaseModel):
    name: str
    legal_form: str | None = None
    address: Address
    vat_id: str | None = None  # Ust-IdNr., EN 16931 BT-31
    tax_number: str | None = None  # Steuernummer, EN 16931 BT-32
    trade_register: str | None = None  # e.g. "Amtsgericht München, HRB 123456"; EN 16931 BT-30
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
    unit: str  # UN/ECE Recommendation 20 unit code, e.g. "HUR", "EA"
    unit_price_net: Decimal
    vat_rate: Decimal  # percent


class Invoice(BaseModel):
    invoice_number: str  # EN 16931 BT-1
    customer: str  # references a Customer file by its filename stem
    issue_date: date  # EN 16931 BT-2
    due_date: date | None = None
    currency: str = Field(pattern=r"^[A-Z]{3}$")  # ISO 4217, EN 16931 BT-5
    buyer_reference: str | None = None  # EN 16931 BT-10
    line_items: list[LineItem]  # EN 16931 BG-25
    notes: str | None = None  # EN 16931 BT-22
