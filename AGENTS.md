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

- PDF content rendering: `playwright`
- PDF merging (background + content): `pypdf`
- EN 16931 XML modeling: `drafthorse`
- XML embedding + PDF/A-3 conversion: `factur-x`
- PDF inspection/attachment extraction: `pikepdf`

## Working style

- Legal/compliance correctness takes priority over feature scope. When in doubt about a EN 16931 field or PDF/A-3
  requirement, flag the uncertainty rather than guessing silently.