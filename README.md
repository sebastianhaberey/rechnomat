# rechnomat

Create invoices compliant with German E-Rechnung laws.

## Installation

```
git clone https://github.com/sebastianhaberey/rechnomat.git
cd rechnomat
pip install .
playwright install chromium
```

Invoice PDFs are rendered by driving a headless Chromium instance (via
[Playwright](https://playwright.dev/python/)) over HTML/CSS templates. `playwright install
chromium` downloads the browser binary Playwright needs; it's a one-time, per-machine step, not a
pip package, and is required before `rechnomat render` will work.

### Getting started

The tool reads `backgrounds/`, `customers/`, `invoices/`, `seller/` and `templates/` from the
current directory, not from the installed package. Before running `rechnomat render`, run
`rechnomat init` inside whichever directory you run `rechnomat` from; it copies these five
folders, pre-filled with example data, from `src/rechnomat/resources/` into the current directory.
Folders that already exist are left untouched, so re-running `init` later only fills in whatever
is still missing; you are notified whether each folder was copied or skipped.

### System dependencies for headless Chromium (Linux only)

On Linux, Chromium also needs a handful of shared libraries that aren't installed by default.
macOS needs no extra step here - skip this section.

**Debian/Ubuntu:**

```
sudo playwright install-deps chromium
```

**Fedora:** `playwright install-deps` only knows how to drive `apt-get`, so on Fedora it fails
outright (`spawn apt-get ENOENT`). Install the equivalent packages with `dnf` instead:

```
sudo dnf install -y atk at-spi2-atk at-spi2-core cups-libs libXcomposite libXdamage libXfixes
```

If `rechnomat render` fails with "Host system is missing dependencies to run browsers",
run `ldd` against the downloaded Chromium binary to see exactly which `.so` is missing:

```
ldd ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | grep "not found"
```

## Usage

```
rechnomat --help
```

## Development

For an editable install with test and lint tooling:

```
pip install -e '.[dev]'
playwright install chromium
```

Tests use the example data and templates bundled in `src/rechnomat/resources/` directly.

```
pytest
ruff check .
ruff format --check .
```

## License

MIT - see [LICENSE](LICENSE).
