# rechnomat

Create invoices compliant with German E-Rechnung laws.

## Installation

### macOS

Using [Homebrew](https://brew.sh/):

```
brew install sebastianhaberey/rechnomat/rechnomat
```

Or with pip (requires Python 3.14+):

```
pip install rechnomat
```

### Linux (Debian / Fedora)

Requires Python 3.14+.

Debian / Ubuntu:

```
sudo apt install python3 python3-pip
pip install rechnomat
```

Fedora:

```
sudo dnf install python3 python3-pip
pip install rechnomat
```

[Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux) is also supported:

```
brew install sebastianhaberey/rechnomat/rechnomat
```

### Windows

Install [Python 3.14+](https://www.python.org/downloads/windows/), then:

```
pip install rechnomat
```

Invoice PDFs are rendered from HTML/CSS templates using
[WeasyPrint](https://weasyprint.org/), a pure-Python PDF rendering engine with no native system
dependencies to install.

## Getting started

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

See [documentation/DEVELOPMENT.md](documentation/DEVELOPMENT.md).

## License

MIT - see [LICENSE](LICENSE).
