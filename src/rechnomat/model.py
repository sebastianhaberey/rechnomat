from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field


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
    country_code: str = Field(pattern=r"^[A-Z]{2}$")  # ISO 3166-1 alpha-2, EN 16931 BT-55


class Contact(BaseModel):
    name: str
    email: str
    phone: str


class Customer(BaseModel):
    name: str
    legal_form: str | None = None
    address: Address
    vat_id: str | None = None  # Ust-IdNr., EN 16931 BT-48
    contact: Contact
    payment_terms_days: int
    notes: str | None = None


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
