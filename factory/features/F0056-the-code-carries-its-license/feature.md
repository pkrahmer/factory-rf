# The code carries its license

## Goal

The factory is licensed under the Apache License 2.0, for its patent grant, with a `NOTICE` file (the human, 2026-11-07). The human changed `LICENSE`, `NOTICE` and `pyproject.toml` on `main`. This feature puts an `SPDX-License-Identifier: Apache-2.0` line into every file of code and every script, so that a file copied out of the repository still says its license, and a guard keeps every new such file in line. Done when its story is merged and `make check` is green.

## Before it starts

F0054 (the documents are rewritten for their readers) is merged. The license change on `main` (commit "The license is Apache 2.0, with a NOTICE file") is in place.

## Scope

- The header in every Python module under `src/factory/` and in every script under `operator/` outside `operator/template/` (S0001).
- A guard that every such file carries it (S0001).
- The README and the decision log name the license (S0001).

## Out of scope

- The tests under `tests/` (the human, 2026-11-07).
- `operator/template/`, which a new project starts from: its files belong to that project, under that project's license.
- `demo/`, whose project is an example with its own files.
- Markdown, YAML, JSON, the generated schemas under `src/factory/contract/`, and the agent files under `agents/`, which tests pin by their text.
- A copyright line in each file: the copyright stands once, in `NOTICE`.

## Stories

- S0001: Every file of code and every script names its license

## The human's changes

- **Before S0001:** done on 2026-11-07: `LICENSE` holds the Apache License 2.0 text from apache.org, `NOTICE` names the product and its copyright, and `pyproject.toml` has `license = "Apache-2.0"` and `license-files = ["LICENSE", "NOTICE"]`.

## Decisions taken for the human

1. **Apache 2.0 instead of MIT** (the human, 2026-11-07), for its explicit patent grant. The dependencies' licenses are unchanged; the allow list in the Makefile is about them, not about the factory's own license.
2. **The header is one line, `SPDX-License-Identifier: Apache-2.0`**, as a comment in the file's own syntax: the first line of a Python module, and the line after the shebang of a script. No copyright line in the files; `NOTICE` holds it once.
3. **Code and scripts, not the tests** (the human, 2026-11-07).
