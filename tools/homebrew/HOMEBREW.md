# Homebrew

## Generate Homebrew Formula

`generate_homebrew_formula.py` needs the `release` dependency group (`requests`, `urllib3`,
`packaging`). Install it from the repository root:

```
pip install '.[release]'
```

The script doesn't install anything itself, so it can run in the normal venv without problems.

To test the script, run it here:

```
python generate_homebrew_formula.py --package rechnomat --version 0.1.0 --python-version 3.14 --template rechnomat.rb.template --output rechnomat.rb
```