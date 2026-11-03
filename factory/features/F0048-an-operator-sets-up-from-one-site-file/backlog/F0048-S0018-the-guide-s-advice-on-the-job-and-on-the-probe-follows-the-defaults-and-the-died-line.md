# The guide's advice on the job and on the probe follows the defaults and the died line

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

S0014 gave `job.sh` the example's sizes as its defaults (decision 21): 4 CPUs, 16Gi, a task timeout of 86400 seconds (24 hours) and 30 idle minutes. S0015 made a `died` run leave its text in the factory log. Three passages of `docs/operator-guide.md` were written before both and now advise against what the factory does:

- *On Cloud Run*, *What the job needs*, **Size**: "Eight vCPUs and 16 GiB of memory at least". The default and the example's `SITE_CPU=4` give half of that, so an operator who keeps the default reads that their job is below the minimum, and one who trusts the guide changes a value the human chose.
- The same list, **The task timeout**: "Set the timeout shorter than the schedule's interval: 23 hours for a daily schedule". The default is now 24 hours, the interval itself, and the passage does not say that a job on a daily schedule must set `SITE_TIMEOUT` below the default.
- *The probe of the agent run*: a flag the pinned `claude` rejects makes "every real run ... end `died` with no text that says why". Since S0015 the factory log names each such run with its text (*A provider's spend limit*, the paragraph *A run that ends `died`*).

This story corrects the three passages so that they say what the factory does. It changes no code, no script and no test, and no default: the defaults are the human's (decision 21). If the human wants eight CPUs as the default instead, refine this story before starting it: then `job.sh`, the example and the rows of S0005's and S0014's tests that pin the defaults change too, and that needs a leave in `feature.md`.

## Interface

None: no module under `src/factory/`, no file under `operator/` or `vm/`, no test changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `operator/`, `vm/`, `image/`, `template/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - *What the job needs*, **Size**: says that the job gets 4 vCPUs and 16 GiB of memory unless `SITE_CPU` and `SITE_MEMORY` say otherwise, and that memory is the limit to raise first, because the root file system, the tmpfs of the image layers, the checkout, the base copy and the workspace all count against it. The words "Eight vCPUs" and "at least" go. The rest of the bullet (the plain base copy, about 1.6 s per GiB for a reset) stays.
   - **The task timeout**: says that the default, 86400 seconds, is the platform's maximum of 24 hours and equals a daily schedule's interval, so a job executed every night sets `SITE_TIMEOUT` below it, such as `23h`. The sentence on two executions that must never overlap stays.
   - *The probe of the agent run*: the parenthesis after "a flag the pinned `claude` rejects" says that every real run would end `died`, each with its line `run <run id> of <work item> (<stage>) died: <text>` in the factory log, instead of "with no text that says why".
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'Eight vCPUs' docs/operator-guide.md; grep -c 'no text that says why' docs/operator-guide.md
```
Expect: `0`, then `0`

```bash
sed -n '/^### What the job needs/,/^### The environment/p' docs/operator-guide.md | grep -c 'SITE_TIMEOUT'
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
