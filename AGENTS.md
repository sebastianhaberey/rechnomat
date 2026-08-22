# AGENTS.md

## Project

A Python application that generates legally compliant German invoices as **ZUGFeRD/Factur-X** files: a PDF/A-3 document
combining a human-readable, visually designed invoice with a machine-readable EN 16931 XML payload embedded inside it.

This exists to prepare for Germany's mandatory B2B e-invoicing rollout (Wachstumschancengesetz): businesses must be able
to receive structured e-invoices already, and issuance becomes mandatory in phases from 2027–2028. A plain PDF invoice
does not satisfy this requirement — only formats like ZUGFeRD, XRechnung, or other EN 16931-conformant formats count as
a valid e-invoice.

## What the app does

1. Takes invoice data (seller, buyer, line items, VAT, totals, dates, etc.).
2. Renders that data as a visual PDF (DIN 5008 letter format), layered on top of a fixed vector letterhead/background
   PDF supplied by the user.
3. Generates a corresponding EN 16931-compliant CII XML representation of the same invoice.
4. Embeds that XML into the visual PDF, converting the result into a conformant PDF/A-3 container — this combined file
   is the final ZUGFeRD/Factur-X invoice.
5. The result should validate cleanly against EN 16931 (e.g. via the ELSTER e-invoice viewer/validator) before being
   considered correct.

## Key constraints to respect

- **No rasterization.** The letterhead background is a vector PDF; it must be merged as native PDF content, never
  flattened to an image, or print quality degrades.
- **XML is the legal source of truth.** Per BMF guidance, if the visual PDF and embedded XML ever disagree, the XML data
  governs for tax purposes — so correctness of the XML fields matters more than visual polish.
- **PDF/A-3 is mandatory for the container**, not just "any PDF with an attachment." Fonts must be embedded, no
  disallowed color spaces/encryption, correct XMP metadata declaring the ZUGFeRD/Factur-X relationship.
- **Cross-platform**: must run on both macOS and Linux. Flag any system-level (non-pip) dependency explicitly.
- Libraries are not guaranteed to produce standards-compliant output by themselves — always validate generated files,
  don't assume correctness.

## Suggested stack

- PDF content rendering: `weasyprint`
- PDF merging (background + content): `pypdf`
- EN 16931 XML modeling: `drafthorse`
- XML embedding + PDF/A-3 conversion: `factur-x`
- PDF inspection/attachment extraction: `pikepdf`

## Working style

- Legal/compliance correctness takes priority over feature scope. When in doubt about a EN 16931 field or PDF/A-3
  requirement, flag the uncertainty rather than guessing silently.

## Future work: special VAT categories

The current implementation (`src/rechnomat/invoice_xml.py`) only supports EN 16931 VAT category **"S" (Standard
rate)** — this covers ordinary German 19%/7% invoices, but not zero-rated, exempt, reverse-charge, or
cross-border cases. `LineItem.vat_rate` (`src/rechnomat/model.py`) is validated to be strictly positive for this
reason; that check is the gate to relax when this is implemented. Findings from researching this, so the next
attempt doesn't have to re-derive them:

- **Relevant category codes** (EN 16931 code list, UNTDID 5305), beyond "S":
  - `Z` — Zero rated goods/services
  - `E` — Exempt from VAT
  - `AE` — VAT reverse charge (domestic)
  - `K` — Intra-community supply (reverse charge, cross-border EU)
  - `G` — Export outside the EU
  - `O` — Not subject to VAT / out of scope
  - (There are a few more in the full list — e.g. Canary Islands/Ceuta/Melilla special regimes — almost certainly
    irrelevant for a German-invoicing app.)
- **Rate constraint per category**: for every category except "S", EN 16931's business rules (BR-Z-01, BR-E-01,
  BR-AE-01, BR-G-01, BR-IC-01, BR-O-01 — one rule per category) require `rate_applicable_percent` to be exactly
  `0`. "S" is the only category where a positive rate is expected. A future `vat_category` field would need to
  enforce this pairing (e.g. via a model validator), not just accept any category with any rate.
- **Exemption reason is mandatory for non-standard categories.** EN 16931 requires either a free-text exemption
  reason (BT-120) or a coded one (BT-121, or both) whenever the category isn't "S" — the exact per-category BR
  rule wasn't verified against the schematron in this session (see the validation gap below), so re-confirm the
  precise requirement (text vs. code vs. either) per category before implementing rather than assuming both are
  always needed. The exemption reason **code** list (BT-121) is the CEF-maintained **VATEX** list (e.g.
  `VATEX-EU-79-C` for a reverse-charge case, `VATEX-EU-G` for export) — not UNTDID.
- **drafthorse already has the plumbing.** `drafthorse.models.accounting.ApplicableTradeTax` — used both for the
  line-level tax (`tradelines.LineSettlement.trade_tax`) and the document-level VAT breakdown
  (`trade.TradeSettlement.trade_tax`) — already exposes `category_code`, `exemption_reason`, and
  `exemption_reason_code` fields. No new drafthorse-side wiring is needed, only using fields that already exist.
- **What would actually need to change:**
  1. `model.py`: add a `vat_category` field (or similar) to `LineItem`, plus a way to carry the exemption
     reason text/code. Relax `LineItem._check_standard_vat_rate` so it only forces `rate > 0` for category "S",
     and instead enforces `rate == 0` + a present exemption reason for the other categories.
  2. `invoice_calc.py`: `compute_totals` currently groups line items into `VatGroup`s keyed by `rate` alone. Two
     lines can both be at `0%` but under different categories (e.g. one export "G", one reverse-charge "AE") and
     must **not** collapse into a single VAT breakdown group — the grouping key needs to become
     `(category_code, rate)` (and probably `exemption_reason_code`, since separate reasons likely need separate
     breakdown lines too).
  3. `invoice_xml.py`: `_apply_line_items`/`_apply_tax_breakdown` currently hardcode
     `_STANDARD_VAT_CATEGORY_CODE = "S"`; both would need to use the per-line category and set
     `exemption_reason`/`exemption_reason_code` on both the line-level and document-level `ApplicableTradeTax`.
- **Validation gap**: this session could only run XSD-level structural validation in-process (no schematron —
  see `documentation/fields.md`), so the exact BR-xx business rules for these categories were not exercised
  end-to-end. Budget for a manual ELSTER-validator round trip (or standing up a schematron/Saxon check) before
  considering this feature done, not just an XSD pass.