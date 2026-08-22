# EN 16931 field coverage

This documents which EN 16931 business terms (BT) and groups (BG) Rechnomat currently populates
in the ZUGFeRD/Factur-X CII XML (`src/rechnomat/invoice_xml.py`), and where each value comes from.
"Source" points to the originating model field (`src/rechnomat/model.py`) or invoice YAML input;
"Constant/derived" means the value isn't user-supplied - it's hardcoded or computed by the app.

Only the EN16931 profile, standard-rate VAT (category "S") is supported - see
[Limitations](#limitations) below.

## Document header

| BT     | Field                       | Source                                            |
|--------|------------------------------|----------------------------------------------------|
| BT-1   | Invoice number               | `invoice_number` argument (derived from the invoice YAML's filename, see `invoice_numbering.py`) |
| BT-2   | Issue date                   | `Invoice.issue_date`                                |
| BT-3   | Invoice type code            | Constant `"380"` (commercial invoice)               |
| BT-5   | Invoice currency code        | `Invoice.currency`                                  |
| BT-9   | Payment due date             | `Invoice.due_date` (computed: `issue_date + payment_terms_days`), when set |
| BT-10  | Buyer reference               | `Invoice.buyer_reference`, when set                 |
| BT-20  | Payment terms (free text)    | Derived: `"Zahlbar bis {due_date}"` when a due date is set, otherwise `"Zahlbar sofort"` (see [BR-CO-25](#br-co-25-payment-terms-fallback)) |
| BT-22  | Invoice note                 | `Invoice.notes`, when set                           |
| BT-24  | Specification identifier     | Constant `"urn:cen.eu:en16931:2017"`                |

## Seller (BG-4)

| BT     | Field                                 | Source                          |
|--------|-----------------------------------------|----------------------------------|
| BT-27  | Seller name                              | `Seller.name`                    |
| BT-30  | Seller legal registration identifier     | `Seller.trade_register`, when set |
| BT-31  | Seller VAT identifier                    | `Seller.vat_id`, when set (EAS scheme `VA`) |
| BT-32  | Seller tax registration identifier       | `Seller.tax_number`, when set (scheme `FC`, German Steuernummer) |
| BT-34  | Seller electronic address                | `Seller.contact.email` (scheme `EM`) |
| BT-35  | Seller address line one                  | `Seller.address.street`          |
| BT-37  | Seller city                              | `Seller.address.city`            |
| BT-38  | Seller post code                         | `Seller.address.postcode`        |
| BT-40  | Seller country code                      | `Seller.address.country_code`    |

`Seller` requires at least one of `vat_id` (BT-31) / `tax_number` (BT-32) to be set (EN 16931
BR-CO-26), enforced by a model validator.

## Buyer (BG-7)

| BT     | Field                             | Source                              |
|--------|--------------------------------------|---------------------------------------|
| BT-44  | Buyer name                           | `Customer.name`                       |
| BT-48  | Buyer VAT identifier                 | `Customer.vat_id`, when set (scheme `VA`) |
| BT-49  | Buyer electronic address             | `Customer.contact.email` (scheme `EM`) |
| BT-50  | Buyer address line one               | `Customer.address.street`             |
| BT-52  | Buyer city                           | `Customer.address.city`               |
| BT-53  | Buyer post code                      | `Customer.address.postcode`           |
| BT-55  | Buyer country code                   | `Customer.address.country_code`       |

## Payment instructions (BG-16/BG-17)

| BT     | Field                              | Source                                  |
|--------|---------------------------------------|-------------------------------------------|
| BT-81  | Payment means type code               | Constant `"58"` (SEPA credit transfer)    |
| BT-84  | Payment account identifier (IBAN)     | `Seller.bank_details.iban`                |
| BT-85  | Payment account name                  | `Seller.bank_details.account_owner`       |
| BT-86  | Payment service provider ID (BIC)     | `Seller.bank_details.bic`                 |

## Line items (BG-25), per `LineItem`

| BT     | Field                        | Source                                                  |
|--------|--------------------------------|------------------------------------------------------------|
| BT-126 | Line identifier                 | Constant/derived: 1-based position in `invoice.line_items` |
| BT-129 | Invoiced quantity                | `LineItem.quantity`                                        |
| BT-130 | Unit of measure code             | `LineItem.unit`                                             |
| BT-131 | Invoice line net amount          | Constant/derived: `quantity * unit_price_net`, rounded (`invoice_calc.compute_totals`) |
| BT-146 | Item net price                   | `LineItem.unit_price_net`                                   |
| BT-151 | Invoiced item VAT category code  | Constant `"S"` (standard rate)                              |
| BT-152 | Invoiced item VAT rate           | `LineItem.vat_rate`                                          |
| BT-153 | Item name                        | `LineItem.description`                                       |

## VAT breakdown (BG-23), one entry per distinct rate

| BT     | Field                         | Source                                                          |
|--------|----------------------------------|----------------------------------------------------------------|
| BT-116 | VAT category taxable amount      | Constant/derived: sum of line net amounts at that rate (`invoice_calc.compute_totals`) |
| BT-117 | VAT category tax amount          | Constant/derived: taxable amount × rate, rounded                |
| BT-118 | VAT category code                | Constant `"S"` (standard rate)                                  |
| BT-119 | VAT category rate                | `LineItem.vat_rate` (grouping key)                               |

## Document totals (BG-22)

| BT     | Field                          | Source                                            |
|--------|-----------------------------------|-----------------------------------------------------|
| BT-106 | Sum of invoice line net amounts    | Constant/derived: `invoice_calc.compute_totals().net_total` |
| BT-109 | Invoice total amount without VAT   | Same as BT-106 (no allowances/charges modeled)       |
| BT-110 | Invoice total VAT amount           | Constant/derived: `invoice_calc.compute_totals().vat_total` |
| BT-112 | Invoice total amount with VAT      | Constant/derived: `invoice_calc.compute_totals().gross_total` |
| BT-115 | Amount due for payment             | Same as BT-112 (no prepayments modeled)              |

## Limitations

- **Standard-rate VAT only.** Every line item's VAT category is emitted as `"S"`; zero-rated,
  exempt, reverse-charge, and other special VAT categories (which need an explicit category code
  and a legal exemption reason, EN 16931 BG-23) are not supported. `LineItem.vat_rate` must be
  positive - enforced by a model validator.
- **Electronic address reuses the contact email.** BT-34/BT-49 use `contact.email` with EAS scheme
  `EM` rather than a dedicated e-invoice routing address (e.g. a Peppol participant ID).
- <a id="br-co-25-payment-terms-fallback"></a>**BR-CO-25 payment-terms fallback.** EN 16931 requires
  either a due date (BT-9) or a payment-terms description (BT-20) whenever an amount is due. Since
  the model has no dedicated free-text payment-terms field, the app always derives one:
  `"Zahlbar bis {due_date}"` when `payment_terms_days` is set, otherwise `"Zahlbar sofort"`.
- **No allowances or charges.** Document-level and line-level allowances/charges (BG-20/BG-21,
  BT-92/BT-99 etc.) aren't modeled, so BT-106/BT-109 and BT-112/BT-115 are always equal pairs.
- **No schematron/business-rule validation in-app.** Only XSD-level structural validation runs
  in-process (via `drafthorse`'s `serialize(schema=...)` and `factur-x`'s `check_xsd`). Full EN
  16931 business-rule (BR-xx) validation - e.g. via the ELSTER e-invoice viewer - is a manual step.
