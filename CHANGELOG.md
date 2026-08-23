# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-23

### Added

- Added support for various VAT categories: S, AE, E, G, O

## [1.0.2] - 2026-08-23

### Fixed

- Better positioning of address

## [1.0.1] - 2026-08-22

### Changed

- Updated documentation for pipx

## [1.0.0] - 2026-08-22

### Added

- Added example PDF to documentation

### Changed

- Template directory now conforms to proper locale code

## [0.5.0] - 2026-08-22

### Changed

- Updated fields documentation
- Addresses now have "address_line_1" through "addres_line_3" instead of "street"
- Command "add" now uses current date for new invoice
- Shortened commands to "add" and "render"
- Added options "--output-directory" / "-o" and "--replace" / "-r" to render command

## [0.4.0] - 2026-08-22

### Fixed

- Seller / buyer contact details were not contained in XML

### Changed

- Invoices are now written to folder "output"

### Removed

- Removed unused parameter "render_address_line" (in invoice)

## [0.3.0] - 2026-08-22

### Added

- Added ZUGFeRD support

## [0.2.0] - 2026-08-18

### Changed

- Switched to WeasyPrint for PDF rendering

## [0.1.0] - 2026-08-18

### Added

- First version (including invoice generation but no ZUGFeERD data)