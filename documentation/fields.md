# EN 16931 field coverage

This documents which EN 16931 business terms (BT) and groups (BG) Rechnomat currently populates
in the ZUGFeRD/Factur-X CII XML, and where each value comes from.
"Source" names where the value comes from: the invoice, seller, or customer YAML input (see
`run/invoices/`, `run/seller/seller.yml`, `run/customers/`), a hardcoded `Constant`, or a
`Derived` value computed by the app. "Field/Value" gives the specific YAML key (nested fields use
dotted paths, e.g. `address.address_line_1`), the constant's value, or a short explanation of how a
derived value is computed.

Only the EN16931 profile, standard-rate VAT (category "S") is supported - see
[Limitations](#limitations) below.

## Document header

| BT     | Field                       | Source        | Field/Value                                            |
|--------|------------------------------|----------------|----------------------------------------------------------|
| BT-1   | Invoice number               | Derived        | Taken from the invoice YAML's filename (e.g. `DE000001.yml` → `DE000001`), not from a field inside the file |
| BT-2   | Issue date                   | Invoice YAML   | `issue_date`                                              |
| BT-3   | Invoice type code            | Constant       | `"380"` (commercial invoice)                               |
| BT-5   | Invoice currency code        | Invoice YAML   | `currency`                                                 |
| BT-9   | Payment due date             | Derived        | `issue_date + payment_terms_days` (invoice YAML fields), when `payment_terms_days` is set |
| BT-10  | Buyer reference               | Invoice YAML   | `buyer_reference`, when set                                |
| BT-20  | Payment terms (free text)    | Derived        | `"Zahlbar bis {due_date}"` when a due date is set, otherwise `"Zahlbar sofort"` (see [BR-CO-25](#br-co-25-payment-terms-fallback)) |
| BT-22  | Invoice note                 | Invoice YAML   | `notes`, when set                                          |
| BT-24  | Specification identifier     | Constant       | `"urn:cen.eu:en16931:2017"`                                 |

## Seller (BG-4)

| BT     | Field                                 | Source      | Field/Value                     |
|--------|------------------------------------------|--------------|------------------------------------|
| BT-27  | Seller name                              | Seller YAML  | `name`                             |
| BT-30  | Seller legal registration identifier     | Seller YAML  | `trade_register`, when set          |
| BT-31  | Seller VAT identifier                    | Seller YAML  | `vat_id`, when set (EAS scheme `VA`) |
| BT-32  | Seller tax registration identifier       | Seller YAML  | `tax_number`, when set (scheme `FC`, German Steuernummer) |
| BT-34  | Seller electronic address                | Seller YAML  | `invoice_email` (scheme `EM`)       |
| BT-35  | Seller address line one                  | Seller YAML  | `address.address_line_1`            |
| BT-36  | Seller address line two                  | Seller YAML  | `address.address_line_2`, when set  |
| BT-162 | Seller address line three                | Seller YAML  | `address.address_line_3`, when set  |
| BT-37  | Seller city                              | Seller YAML  | `address.city`                      |
| BT-38  | Seller post code                         | Seller YAML  | `address.postcode`                  |
| BT-40  | Seller country code                      | Seller YAML  | `address.country_code`              |

The seller YAML must set at least one of `vat_id` (BT-31) / `tax_number` (BT-32) (EN 16931
BR-CO-26), enforced by a model validator.

## Buyer (BG-7)

| BT     | Field                             | Source        | Field/Value                          |
|--------|--------------------------------------|----------------|-----------------------------------------|
| BT-44  | Buyer name                           | Customer YAML  | `name`                                  |
| BT-48  | Buyer VAT identifier                 | Customer YAML  | `vat_id`, when set (scheme `VA`)         |
| BT-49  | Buyer electronic address             | Customer YAML  | `invoice_email` (scheme `EM`)            |
| BT-50  | Buyer address line one               | Customer YAML  | `address.address_line_1`                 |
| BT-51  | Buyer address line two               | Customer YAML  | `address.address_line_2`, when set       |
| BT-163 | Buyer address line three             | Customer YAML  | `address.address_line_3`, when set       |
| BT-52  | Buyer city                           | Customer YAML  | `address.city`                           |
| BT-53  | Buyer post code                      | Customer YAML  | `address.postcode`                       |
| BT-55  | Buyer country code                   | Customer YAML  | `address.country_code`                   |

## Payment instructions (BG-16/BG-17)

| BT     | Field                              | Source        | Field/Value                              |
|--------|---------------------------------------|----------------|----------------------------------------------|
| BT-81  | Payment means type code               | Constant       | `"58"` (SEPA credit transfer)                |
| BT-84  | Payment account identifier (IBAN)     | Seller YAML    | `bank_details.iban`                          |
| BT-85  | Payment account name                  | Seller YAML    | `bank_details.account_owner`                 |
| BT-86  | Payment service provider ID (BIC)     | Seller YAML    | `bank_details.bic`                           |

## Line items (BG-25), per invoice YAML `line_items` entry

| BT     | Field                        | Source        | Field/Value                                             |
|--------|--------------------------------|----------------|--------------------------------------------------------------|
| BT-126 | Line identifier                 | Derived        | 1-based position of the entry in `line_items`                |
| BT-129 | Invoiced quantity                | Invoice YAML   | `line_items[].quantity`                                       |
| BT-130 | Unit of measure code             | Invoice YAML   | `line_items[].unit`                                            |
| BT-131 | Invoice line net amount          | Derived        | `quantity * unit_price_net`, rounded to cents                 |
| BT-146 | Item net price                   | Invoice YAML   | `line_items[].unit_price_net`                                  |
| BT-151 | Invoiced item VAT category code  | Constant       | `"S"` (standard rate)                                          |
| BT-152 | Invoiced item VAT rate           | Invoice YAML   | `line_items[].vat_rate`                                        |
| BT-153 | Item name                        | Invoice YAML   | `line_items[].description`                                     |

## VAT breakdown (BG-23), one entry per distinct rate

| BT     | Field                         | Source        | Field/Value                                                     |
|--------|----------------------------------|----------------|----------------------------------------------------------------------|
| BT-116 | VAT category taxable amount      | Derived        | Sum of line net amounts (BT-131) at that rate                        |
| BT-117 | VAT category tax amount          | Derived        | Taxable amount (BT-116) × rate, rounded to cents                     |
| BT-118 | VAT category code                | Constant       | `"S"` (standard rate)                                                |
| BT-119 | VAT category rate                | Invoice YAML   | `line_items[].vat_rate` (grouping key)                               |

## Document totals (BG-22)

| BT     | Field                          | Source     | Field/Value                                       |
|--------|-----------------------------------|-------------|-------------------------------------------------------|
| BT-106 | Sum of invoice line net amounts    | Derived     | Sum of all line net amounts (BT-131)                   |
| BT-109 | Invoice total amount without VAT   | Derived     | Same as BT-106 (no allowances/charges modeled)         |
| BT-110 | Invoice total VAT amount           | Derived     | Sum of all VAT category tax amounts (BT-117)           |
| BT-112 | Invoice total amount with VAT      | Derived     | BT-109 + BT-110                                        |
| BT-115 | Amount due for payment             | Derived     | Same as BT-112 (no prepayments modeled)                |

## Limitations

- **Standard-rate VAT only.** Every line item's VAT category is emitted as `"S"`; zero-rated,
  exempt, reverse-charge, and other special VAT categories (which need an explicit category code
  and a legal exemption reason, EN 16931 BG-23) are not supported. `vat_rate` must be positive in
  every line item - enforced by a model validator.
- **Electronic address is always an email, not a Peppol ID.** BT-34/BT-49 are populated from
  `invoice_email` (seller/customer YAML) with EAS scheme `EM`, rather than a dedicated e-invoice
  routing address (e.g. a Peppol participant ID). `invoice_email` is kept separate from
  `contact.email` since the address invoices are sent to/from (e.g. an accounts-payable or
  `rechnungen@` mailbox) is often different from the named contact's own email.
- <a id="br-co-25-payment-terms-fallback"></a>**BR-CO-25 payment-terms fallback.** EN 16931 requires
  either a due date (BT-9) or a payment-terms description (BT-20) whenever an amount is due. Since
  the invoice YAML has no dedicated free-text payment-terms field, the app always derives one:
  `"Zahlbar bis {due_date}"` when `payment_terms_days` is set, otherwise `"Zahlbar sofort"`.
- **No allowances or charges.** Document-level and line-level allowances/charges (BG-20/BG-21,
  BT-92/BT-99 etc.) aren't modeled, so BT-106/BT-109 and BT-112/BT-115 are always equal pairs.
- **No schematron/business-rule validation in-app.** Only XSD-level structural validation runs
  in-process (via `drafthorse`'s `serialize(schema=...)` and `factur-x`'s `check_xsd`). Full EN
  16931 business-rule (BR-xx) validation - e.g. via the ELSTER e-invoice viewer - is a manual step.
