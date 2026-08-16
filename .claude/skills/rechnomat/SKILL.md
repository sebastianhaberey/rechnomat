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
