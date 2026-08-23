from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.note import IncludedNote
from drafthorse.models.party import PostalTradeAddress, TaxRegistration, TradeParty
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem as XmlLineItem

from rechnomat.invoice_calc import InvoiceTotals, LineItemAmount, VatGroup, compute_totals
from rechnomat.model import STANDARD_VAT_CATEGORY_CODE, Address, Contact, Customer, Invoice, Seller

_GUIDELINE_PARAMETER_ID = "urn:cen.eu:en16931:2017"
_INVOICE_TYPE_CODE = "380"
_VAT_TYPE_CODE = "VAT"
_SEPA_CREDIT_TRANSFER_TYPE_CODE = "58"
_EMAIL_SCHEME_ID = "EM"
_VAT_SCHEME_ID = "VA"
_TAX_NUMBER_SCHEME_ID = "FC"

# (exemption_reason_code [BT-121, VATEX codelist], exemption_reason [BT-120, free text]) per
# non-standard VAT category - fixed, machine-facing text; independent of the human-facing legal
# note the seller writes into Invoice.notes for the printed page
_VAT_EXEMPTION_TEXT_BY_CATEGORY: dict[str, tuple[str, str]] = {
    "AE": ("VATEX-EU-AE", "Reverse charge"),
    "E": ("VATEX-EU-E", "Exempt from VAT"),
    "G": ("VATEX-EU-G", "Export outside the EU"),
    "O": ("VATEX-EU-O", "Not subject to VAT"),
}


def build_invoice_xml(*, invoice: Invoice, invoice_number: str, customer: Customer, seller: Seller) -> bytes:
    """
    Build an EN 16931-conformant CII (Cross-Industry Invoice) XML representation of `invoice`,
    validated against the Factur-X EN16931 profile XSD. Returns UTF-8 XML bytes ready for
    embedding into a PDF/A-3 container - see invoice_pdf.embed_invoice_xml for that step.
    """
    totals = compute_totals(invoice)

    doc = Document()
    _apply_header(doc, invoice=invoice, invoice_number=invoice_number)
    _apply_seller(doc, seller)
    _apply_buyer(doc, customer)
    if invoice.buyer_reference:
        doc.trade.agreement.buyer_reference = invoice.buyer_reference

    doc.trade.settlement.currency_code = invoice.currency
    _apply_line_items(doc, totals.line_amounts)
    _apply_tax_breakdown(doc, totals.vat_groups)
    _apply_payment(doc, invoice=invoice, seller=seller)
    _apply_monetary_summation(doc, invoice=invoice, totals=totals)

    return doc.serialize(schema="FACTUR-X_EN16931")


def _apply_header(doc: Document, *, invoice: Invoice, invoice_number: str) -> None:
    # never set doc.header.name/languages - the Factur-X EN16931 XSD doesn't allow them, even
    # though drafthorse's Header class exposes both
    doc.context.guideline_parameter.id = _GUIDELINE_PARAMETER_ID
    doc.header.id = invoice_number
    doc.header.type_code = _INVOICE_TYPE_CODE
    doc.header.issue_date_time = invoice.issue_date
    if invoice.notes:
        note = IncludedNote()
        note.content = invoice.notes
        doc.header.notes.add(note)


def _apply_seller(doc: Document, seller: Seller) -> None:
    party = doc.trade.agreement.seller
    party.name = seller.name
    _apply_address(party, seller.address)
    _apply_contact(party, seller.contact)
    party.electronic_address.uri_ID = (_EMAIL_SCHEME_ID, seller.invoice_email)
    if seller.trade_register:
        party.legal_organization.id = seller.trade_register
    if seller.vat_id:
        _add_tax_registration(party, _VAT_SCHEME_ID, seller.vat_id)
    if seller.tax_number:
        _add_tax_registration(party, _TAX_NUMBER_SCHEME_ID, seller.tax_number)


def _apply_buyer(doc: Document, customer: Customer) -> None:
    party = doc.trade.agreement.buyer
    party.name = customer.name
    _apply_address(party, customer.address)
    _apply_contact(party, customer.contact)
    party.electronic_address.uri_ID = (_EMAIL_SCHEME_ID, customer.invoice_email)
    if customer.vat_id:
        _add_tax_registration(party, _VAT_SCHEME_ID, customer.vat_id)


def _apply_contact(party: TradeParty, contact: Contact) -> None:
    party.contact.person_name = contact.name
    party.contact.telephone.number = contact.phone
    party.contact.email.address = contact.email


def _apply_address(party: TradeParty, address: Address) -> None:
    postal_address: PostalTradeAddress = party.address
    postal_address.line_one = address.address_line_1
    if address.address_line_2:
        postal_address.line_two = address.address_line_2
    if address.address_line_3:
        postal_address.line_three = address.address_line_3
    postal_address.postcode = address.postcode
    postal_address.city_name = address.city
    postal_address.country_id = address.country_code


def _add_tax_registration(party: TradeParty, scheme_id: str, value: str) -> None:
    registration = TaxRegistration()
    registration.id = (scheme_id, value)
    party.tax_registrations.add(registration)


def _apply_line_items(doc: Document, line_amounts: list[LineItemAmount]) -> None:
    for index, line in enumerate(line_amounts, start=1):
        item = line.item
        xml_item = XmlLineItem()
        xml_item.document.line_id = str(index)
        xml_item.product.name = item.description
        xml_item.agreement.net.amount = item.unit_price_net
        xml_item.delivery.billed_quantity = (item.quantity, item.unit)
        xml_item.settlement.trade_tax.type_code = _VAT_TYPE_CODE
        xml_item.settlement.trade_tax.category_code = item.vat_category_code
        xml_item.settlement.trade_tax.rate_applicable_percent = item.vat_rate
        xml_item.settlement.monetary_summation.total_amount = line.net_amount
        doc.trade.items.add(xml_item)


def _apply_tax_breakdown(doc: Document, vat_groups: list[VatGroup]) -> None:
    for group in vat_groups:
        tax = ApplicableTradeTax()
        tax.calculated_amount = group.vat_amount
        tax.type_code = _VAT_TYPE_CODE
        tax.basis_amount = group.net_amount
        tax.category_code = group.category_code
        tax.rate_applicable_percent = group.rate
        if group.category_code != STANDARD_VAT_CATEGORY_CODE:
            reason_code, reason_text = _VAT_EXEMPTION_TEXT_BY_CATEGORY[group.category_code]
            tax.exemption_reason_code = reason_code
            tax.exemption_reason = reason_text
        doc.trade.settlement.trade_tax.add(tax)


def _apply_payment(doc: Document, *, invoice: Invoice, seller: Seller) -> None:
    means = PaymentMeans()
    means.type_code = _SEPA_CREDIT_TRANSFER_TYPE_CODE
    means.payee_account.iban = seller.bank_details.iban
    means.payee_account.account_name = seller.bank_details.account_owner
    means.payee_institution.bic = seller.bank_details.bic
    doc.trade.settlement.payment_means.add(means)

    terms = PaymentTerms()
    if invoice.due_date:
        # EN 16931 BR-CO-25: an invoice with an amount due needs either a due date (BT-9) or a
        # payment-terms description (BT-20) - always emit the description too, in German, since
        # the model doesn't otherwise carry free-text payment terms
        terms.description = f"Zahlbar bis {invoice.due_date.strftime('%d.%m.%Y')}"
        terms.due = invoice.due_date
    else:
        terms.description = "Zahlbar sofort"
    doc.trade.settlement.terms.add(terms)


def _apply_monetary_summation(doc: Document, *, invoice: Invoice, totals: InvoiceTotals) -> None:
    summation = doc.trade.settlement.monetary_summation
    summation.line_total = totals.net_total
    summation.tax_basis_total = (totals.net_total, invoice.currency)
    summation.tax_total = (totals.vat_total, invoice.currency)
    summation.grand_total = (totals.gross_total, invoice.currency)
    summation.due_amount = totals.gross_total
