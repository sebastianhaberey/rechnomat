---
name: rechnomat
description: Ground rules for working on the rechnomat codebase (Python invoicing tool) - git discipline and code generation standards. Use for any task that changes files in this repo.
---

# rechnomat

Ground rules for working in this repository.

## Plans

- When in planning mode, write the plan to `.claude/plans` for the user to open and review.

## General

- Never commit anything, under any circumstances. Leave changes staged/unstaged for the user to review and commit
  themselves.
- Never push or pull. Do not run `git push`, `git pull`, or `git fetch` against any remote.

## Code Generation

- Verify all changes with `ruff` (lint and format) before considering a change done:
  ```
  ruff check .
  ruff format --check .
  ```
- Verify all changes by running the test suite:
  ```
  pytest
  ```
- Design functionality for testability. Prefer small, decoupled units (pure functions, clear interfaces) over designs
  that are hard to exercise in isolation.
- New functionality must come with appropriate tests covering the new behavior, including relevant edge cases.

## Verifying Layout/Template Changes

Passing tests do not confirm a layout looks right - changes to `src/rechnomat/resources/templates/de/` (HTML/CSS)
must be checked visually before considering the change done:

1. Render sample invoice HTML with `render_invoice_html` (see `tests/test_invoice_html.py` or
   `tests/test_invoice_pdf.py` for ready-made `CUSTOMER`/`SELLER`/`BASE_INVOICE` fixtures) and write the result to a
   file in the scratchpad directory.
2. Screenshot that HTML file with Playwright (already a project dependency), e.g.:
   ```python
   from playwright.sync_api import sync_playwright

   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page(viewport={"width": 900, "height": 1300})
       page.goto("file:///path/to/preview.html")
       page.screenshot(path="/path/to/preview.png", full_page=True)
       browser.close()
   ```
3. View the PNG with the Read tool to inspect the rendered layout.
4. Delete the temporary preview files from the scratchpad when done.
