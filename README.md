# Rechnomat

Create invoices compliant with German E-Rechnung laws.

## Installation

### Prerequisites

This application requires Python >= 3.14 installed. Please refer
to [their documentation](https://www.python.org/downloads/) on how to install Python for your system.

It also uses [WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) to render PDFs,
which requires some native libraries.

#### macOS

```
brew install pango
```

Homebrew's libraries aren't on macOS's default library search path, so also add this to your shell
profile (e.g. `~/.zshrc`):

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
python3 -m venv .venv
source .venv/bin/activate
pip install rechnomat
```

## Getting started

Go to a working directory of your choice, then initialize it:

```
rechnomat init
```

This will create subfolders for customers, invoices etc. The folders contain demo files that you can use as templates.
Render the demo invoice with:

```
rechnomat render-invoice
```

## Development

See [documentation/DEVELOPMENT.md](documentation/DEVELOPMENT.md).

## License

MIT - see [LICENSE](LICENSE).
