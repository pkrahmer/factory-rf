# Every file of code and every script names its license

## Description

The factory is licensed under the Apache License 2.0 (the human changed `LICENSE`, `NOTICE` and `pyproject.toml` on 2026-11-07). A file copied out of the repository does not say so today. This story adds the line `SPDX-License-Identifier: Apache-2.0`, as a comment, to every Python module under `src/factory/` and to every script under `operator/` outside `operator/template/`. It adds a guard that fails when such a file lacks the line, so that every new file carries it. The tests, `operator/template/`, `demo/`, the documents and the agent files get no header. The code's behaviour does not change.

## Interface

- The header is the comment line `# SPDX-License-Identifier: Apache-2.0`:
  - in each Python module under `src/factory/` (186 files today), as its first line, before the module docstring;
  - in each script under `operator/` outside `operator/template/` (18 files today: `operator/bin/sanitise`, `operator/bin/site`, `operator/job/job.sh`, `operator/lib/hosting.sh`, `operator/lib/site.sh`, the nine scripts under `operator/skill/kumpel/scripts/`, `operator/vm/Dockerfile`, `operator/vm/git-credential-factory`, `operator/vm/job-start.sh` and `operator/vm/setup.sh`), as the line right after the shebang, or as the first line where there is none (`operator/vm/Dockerfile`).
  - The coder adds the headers, by a script it runs once, and changes nothing else in those files.
- `tests/guards/test_license_headers.py` (new): every tracked file in that scope carries the header on its first line, or on the line after its shebang. The scope is read from `git ls-files`: the `*.py` files under `src/factory/`, and the files under `operator/` outside `operator/template/` that are a `*.sh` file, a Dockerfile, or start with `#!`. A file that lacks it gives its path in the failure. One more test shows that a file under `tests/` or `operator/template/` is outside the scope.
- The human's leave: an earlier test whose only failure is the one added header line, for example a test that reads a script's first lines or its header comment, may be changed so far as that line requires; every changed test keeps its name and what it checks, and the entry names each one. The tester makes these changes in its first run, before the coder adds the headers.
- `src/factory/contract/*.schema.json` are JSON and get no header; the contract's generation does not change.

## Acceptance criteria

1. The guard passes on the branch: every file in its scope carries the header in its place.
2. The guard fails, naming the file, for a Python module under `src/factory/` without the header, and for a script with a shebang whose header stands on its first line instead of after the shebang (rows of one test on files the test writes under `tmp_path`).
3. A file under `tests/` and one under `operator/template/` are outside the guard's scope (rows of one test).
4. Every script still runs: `sh -n` on each `*.sh` script and `bash -n` on each `#!/bin/bash` script in the scope exits 0 (one test).
5. `make check` stays green.
6. docs: `README.md`: the reader learns that the factory is licensed under the Apache License 2.0, with a link to `LICENSE` and `NOTICE`. `docs/project-guide/README.md`: the guard among the guards, and that a new module or script carries the header. `docs/decisions.md`: one entry for the feature's decisions 1 to 3, with the rejected option of a copyright line in every file.

## Smoke test

```bash
git ls-files 'src/factory/*.py' | while read f; do head -1 "$f"; done | grep -vc "^# SPDX-License-Identifier: Apache-2.0$"
```
Expect: `0`

## Journal
