# Development

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
