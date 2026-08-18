# rechnomat

Create invoices compliant with German E-Rechnung laws.

## Installation

```
git clone https://github.com/sebastianhaberey/rechnomat.git
cd rechnomat
pip install .
```

Invoice PDFs are rendered from HTML/CSS templates using
[WeasyPrint](https://weasyprint.org/), a pure-Python PDF rendering engine with no native system
dependencies to install.

### Getting started

The tool reads `backgrounds/`, `customers/`, `invoices/`, `seller/` and `templates/` from the
current directory, not from the installed package. Before running `rechnomat render-invoice`, run
`rechnomat init` inside whichever directory you run `rechnomat` from; it copies these five
folders, pre-filled with example data, from `src/rechnomat/resources/` into the current directory.
Folders that already exist are left untouched, so re-running `init` later only fills in whatever
is still missing; you are notified whether each folder was copied or skipped.

## Usage

```
rechnomat --help
```

## Development

For an editable install with test and lint tooling:

```
pip install -e '.[dev]'
```

Tests use the example data and templates bundled in `src/rechnomat/resources/` directly.

```
pytest
ruff check .
ruff format --check .
```

## License

MIT - see [LICENSE](LICENSE).
