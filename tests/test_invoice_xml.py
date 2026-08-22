from lxml import etree
from pydantic import ValidationError
from test_invoice_pdf import BASE_INVOICE, CUSTOMER, SELLER

from rechnomat.invoice_calc import compute_totals
from rechnomat.invoice_xml import build_invoice_xml
from rechnomat.model import Invoice, LineItem

NS = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
}


def _xpath(root, path):
    return root.xpath(path, namespaces=NS)


def test_build_invoice_xml_produces_schema_valid_xml():
    invoice = Invoice.model_validate(BASE_INVOICE)

    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)

    assert xml_bytes.startswith(b"<?xml")


def test_build_invoice_xml_maps_seller_and_buyer_fields():
    invoice = Invoice.model_validate(BASE_INVOICE)

    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)
    root = etree.fromstring(xml_bytes)

    seller_party = _xpath(root, "//ram:SellerTradeParty")[0]
    assert _xpath(seller_party, "ram:Name/text()")[0] == SELLER.name
    assert _xpath(seller_party, "ram:PostalTradeAddress/ram:LineOne/text()")[0] == SELLER.address.street
    vat_id = _xpath(seller_party, "ram:SpecifiedTaxRegistration/ram:ID[@schemeID='VA']/text()")[0]
    assert vat_id == SELLER.vat_id
    seller_email = _xpath(seller_party, "ram:URIUniversalCommunication/ram:URIID[@schemeID='EM']/text()")[0]
    assert seller_email == SELLER.invoice_email
    seller_contact = _xpath(seller_party, "ram:DefinedTradeContact")[0]
    assert _xpath(seller_contact, "ram:PersonName/text()")[0] == SELLER.contact.name
    assert (
        _xpath(seller_contact, "ram:TelephoneUniversalCommunication/ram:CompleteNumber/text()")[0]
        == SELLER.contact.phone
    )
    assert _xpath(seller_contact, "ram:EmailURIUniversalCommunication/ram:URIID/text()")[0] == SELLER.contact.email

    buyer_party = _xpath(root, "//ram:BuyerTradeParty")[0]
    assert _xpath(buyer_party, "ram:Name/text()")[0] == CUSTOMER.name
    buyer_email = _xpath(buyer_party, "ram:URIUniversalCommunication/ram:URIID[@schemeID='EM']/text()")[0]
    assert buyer_email == CUSTOMER.invoice_email
    buyer_contact = _xpath(buyer_party, "ram:DefinedTradeContact")[0]
    assert _xpath(buyer_contact, "ram:PersonName/text()")[0] == CUSTOMER.contact.name
    assert (
        _xpath(buyer_contact, "ram:TelephoneUniversalCommunication/ram:CompleteNumber/text()")[0]
        == CUSTOMER.contact.phone
    )
    assert _xpath(buyer_contact, "ram:EmailURIUniversalCommunication/ram:URIID/text()")[0] == CUSTOMER.contact.email


def test_build_invoice_xml_maps_line_items_and_tax_breakdown():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                *BASE_INVOICE["line_items"],
                {"description": "Books", "quantity": "2", "unit": "EA", "unit_price_net": "10.00", "vat_rate": "7"},
            ],
        }
    )

    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)
    root = etree.fromstring(xml_bytes)

    line_items = _xpath(root, "//ram:IncludedSupplyChainTradeLineItem")
    assert len(line_items) == 2

    tax_breakdown = _xpath(root, "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax")
    assert len(tax_breakdown) == 2
    for tax in tax_breakdown:
        assert _xpath(tax, "ram:CategoryCode/text()")[0] == "S"


def test_build_invoice_xml_maps_monetary_summation():
    invoice = Invoice.model_validate(
        {
            **BASE_INVOICE,
            "line_items": [
                *BASE_INVOICE["line_items"],
                {"description": "Books", "quantity": "2", "unit": "EA", "unit_price_net": "10.00", "vat_rate": "7"},
            ],
        }
    )
    totals = compute_totals(invoice)

    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)
    root = etree.fromstring(xml_bytes)

    summation = _xpath(root, "//ram:SpecifiedTradeSettlementHeaderMonetarySummation")[0]
    assert _xpath(summation, "ram:LineTotalAmount/text()")[0] == str(totals.net_total)
    assert _xpath(summation, "ram:TaxBasisTotalAmount/text()")[0] == str(totals.net_total)
    assert _xpath(summation, "ram:TaxTotalAmount/text()")[0] == str(totals.vat_total)
    assert _xpath(summation, "ram:GrandTotalAmount/text()")[0] == str(totals.gross_total)
    assert _xpath(summation, "ram:DuePayableAmount/text()")[0] == str(totals.gross_total)


def test_build_invoice_xml_falls_back_to_payment_terms_description_when_due_date_missing():
    invoice = Invoice.model_validate(BASE_INVOICE)
    assert invoice.due_date is None

    xml_bytes = build_invoice_xml(invoice=invoice, invoice_number="00000001", customer=CUSTOMER, seller=SELLER)
    root = etree.fromstring(xml_bytes)

    description = _xpath(root, "//ram:SpecifiedTradePaymentTerms/ram:Description/text()")[0]
    assert description


def test_line_item_rejects_non_positive_vat_rate():
    base = BASE_INVOICE["line_items"][0]

    for rate in ("0", "-1"):
        try:
            LineItem.model_validate({**base, "vat_rate": rate})
        except ValidationError:
            continue
        raise AssertionError(f"expected ValidationError for vat_rate={rate}")
