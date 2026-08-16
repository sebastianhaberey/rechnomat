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
pip package, and is required before `rechnomat render-invoice` will work.

### Templates

The tool loads templates from `<run directory>/templates/`, not from the installed package. The
canonical copy lives in `src/rechnomat/resources/templates/`; before running `rechnomat
render-invoice`, copy that directory (including `fonts/`) to `templates/` inside whichever
directory you run `rechnomat` from.

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

If `rechnomat render-invoice` fails with "Host system is missing dependencies to run browsers",
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

Tests use the template copy in `src/rechnomat/resources/templates/` directly.

```
pytest
ruff check .
ruff format --check .
```

## License

MIT - see [LICENSE](LICENSE).
