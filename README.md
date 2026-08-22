# Rechnomat

Create invoices compliant with German E-Rechnung laws.

## Installation

### Prerequisites

Rechnomat requires Python >= 3.14 installed. Please refer to [their documentation](https://www.python.org/downloads/) on
how to install Python on your system.

The application also uses [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) to
render PDFs, which requires some native libraries.

#### macOS

```
brew install pango
```

Homebrew's libraries aren't on macOS's default library search path, so also add this to your shell profile (e.g.
`~/.zshrc`):

```
export DYLD_LIBRARY_PATH="$(brew --prefix)/lib"
```

#### Linux

##### Ubuntu / Debian

```
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

##### Fedora

```
sudo dnf install pango
```

#### Windows

Install the [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases), then
make sure its `bin` folder is on your `PATH`.

### Rechnomat

Install Rechnomat itself into a virtual environment:

```
mkdir rechnomat
cd rechnomat
python3 -m venv .venv
source .venv/bin/activate
pip install rechnomat
```

Whenever you re-open your terminal, you need to re-source rechnomat:

```
cd rechnomat
source .venv/bin/activate
```

## Getting started

Go to a working directory of your choice, then initialize it:

```
rechnomat init
```

This will create subfolders for customers, invoices etc. The folders contain demo files that you can use as templates.
Render the demo invoice to folder `output` with:

```
rechnomat render-invoice
```

## Disclaimer

Even though I'm doing my best, there's **no guarantee at all** that this application will generate correct invoices. To
make sure that the generated invoice contains all the information you want, upload it at
the [Elster E-Rechnung Page](https://www.elster.de/eportal/e-rechnung) and check the information for correctness.

## License

MIT - see [LICENSE](LICENSE).