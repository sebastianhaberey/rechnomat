# Rechnomat

Creates invoices compliant with German E-Rechnung laws.

[Example PDF](documentation/example.pdf)

## Installation

### Prerequisites

Make sure you have the following dependencies installed:

- [Python >= 3.14](https://www.python.org/downloads/)
- [Pipx](https://pipx.pypa.io/latest/how-to/install-pipx.html)

### WeasyPrint

[WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/index.html) will be installed with Rechnomat, but you may
need to install some libraries it requires, depending on your OS.

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

Install Rechnomat itself with [pipx](https://pipx.pypa.io/stable/installation/):

```
pipx install rechnomat
```

## Getting started

Go to a working directory of your choice and initialize it:

```
rechnomat init
```

This will create subfolders with working example files. Render the example invoice with:

```
rechnomat render
```

The rendered invoice will appear in the output folder. Now edit the seller, customer and invoice files with your own
data and render again. When required, you may add new invoices using:

```
rechnomat add [customer]
```

where `[customer]` is the name of the customer file. The command will duplicate the most recent existing invoice for
that customer, i.e. the invoice with the highest number. If you don't specify the customer, the command will duplicate
the most recent existing invoice. If there is no existing invoice, the command will duplicate the example.

The new invoice will have the next logical invoice number in sequence and the current date. You can also create a new
invoice by manually copying an existing invoice file. The same goes for customers: create new customers by copying
existing files.

Use

```
rechnomat --help
```

to show all available commands and options.

## Disclaimer

Even though I'm doing my best, there's **no guarantee at all** that this application will generate correct invoices. To
make sure that the generated invoice contains all the information you want, upload it at
the [Elster E-Rechnung Page](https://www.elster.de/eportal/e-rechnung) and check the information for correctness.

## License

MIT - see [LICENSE](LICENSE).