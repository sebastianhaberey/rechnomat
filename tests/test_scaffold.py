from datetime import date
from decimal import Decimal

import pytest
from pydantic import BaseModel, Field

from rechnomat.model import Customer, Invoice
from rechnomat.scaffold import render_scaffold

EXPECTED_CUSTOMER_SCAFFOLD = """\
name: ""
legal_form: ""
address:
  street: ""
  postcode: ""
  city: ""
  country_code: ""  # ISO 3166-1 alpha-2, EN 16931 BT-55
vat_id: ""  # Ust-IdNr., EN 16931 BT-48
contact:
  name: ""
  email: ""
  phone: ""
payment_terms_days: 0
notes: ""
"""


def test_render_scaffold_for_customer_model():
    assert render_scaffold(Customer) == EXPECTED_CUSTOMER_SCAFFOLD


def test_render_scaffold_applies_top_level_override():
    result = render_scaffold(Customer, overrides={"name": "Acme Test GmbH"})
    lines = result.splitlines()
    assert lines[0] == 'name: "Acme Test GmbH"'
    assert lines[1:] == EXPECTED_CUSTOMER_SCAFFOLD.splitlines()[1:]


def test_render_scaffold_escapes_quotes_and_backslashes_in_override():
    result = render_scaffold(Customer, overrides={"name": 'Quote " and backslash \\'})
    assert result.splitlines()[0] == 'name: "Quote \\" and backslash \\\\"'


def test_render_scaffold_for_invoice_model():
    result = render_scaffold(Invoice, overrides={"invoice_number": "0000123", "customer": "acme-gmbh"})
    today = date.today().isoformat()
    assert result == (
        'invoice_number: "0000123"  # EN 16931 BT-1\n'
        'customer: "acme-gmbh"  # references a Customer file by its filename stem\n'
        f"issue_date: {today}  # EN 16931 BT-2\n"
        f"due_date: {today}\n"
        'currency: ""  # ISO 4217, EN 16931 BT-5\n'
        'buyer_reference: ""  # EN 16931 BT-10\n'
        "line_items:  # EN 16931 BG-25\n"
        '  - description: ""\n'
        '    quantity: "0"\n'
        '    unit: ""  # UN/ECE Recommendation 20 unit code, e.g. "HUR", "EA"\n'
        '    unit_price_net: "0"\n'
        '    vat_rate: "0"  # percent\n'
        'notes: ""  # EN 16931 BT-22\n'
    )


def test_render_scaffold_raises_for_unsupported_scalar_type():
    class Unsupported(BaseModel):
        amount: float

    with pytest.raises(NotImplementedError):
        render_scaffold(Unsupported)


def test_render_scaffold_placeholder_for_date_is_today():
    class HasDate(BaseModel):
        issue_date: date

    result = render_scaffold(HasDate)
    assert result == f"issue_date: {date.today().isoformat()}\n"


def test_render_scaffold_placeholder_for_decimal_is_quoted():
    class HasDecimal(BaseModel):
        amount: Decimal

    assert render_scaffold(HasDecimal) == 'amount: "0"\n'


def test_render_scaffold_renders_list_of_model_as_one_example_item():
    class Item(BaseModel):
        description: str
        amount: Decimal

    class HasList(BaseModel):
        items: list[Item] = Field(description="line items")

    assert render_scaffold(HasList) == ('items:  # line items\n  - description: ""\n    amount: "0"\n')


def test_render_scaffold_raises_for_list_of_unsupported_type():
    class HasList(BaseModel):
        tags: list[str]

    with pytest.raises(NotImplementedError):
        render_scaffold(HasList)


def test_render_scaffold_raises_for_optional_list():
    class Item(BaseModel):
        value: str

    class HasOptionalList(BaseModel):
        items: list[Item] | None = None

    with pytest.raises(NotImplementedError):
        render_scaffold(HasOptionalList)


def test_render_scaffold_raises_for_optional_nested_model():
    class Nested(BaseModel):
        value: str

    class Unsupported(BaseModel):
        nested: Nested | None = None

    with pytest.raises(NotImplementedError):
        render_scaffold(Unsupported)


def test_render_scaffold_omits_comment_when_description_absent():
    class Plain(BaseModel):
        required_field: int
        optional_field: int | None = Field(default=None)

    result = render_scaffold(Plain)
    assert result == "required_field: 0\noptional_field: 0\n"
