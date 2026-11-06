---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 585
comments_read: [6674965185]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T02:12:38.509322Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T02:07:39.817288Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T02:07:39.823711Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T02:08:03.973696Z'
  stage: intake
  run: 416fb2a0fb164644bdf623d0c0bed8ba
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T02:12:05.409785Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T02:12:08.113561Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T02:12:32.622625Z'
  stage: intake
  run: a1db2cd2f186412e9bd23f987a89d05c
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T02:12:38.509322Z'
  stage: tests
---

# Every name a document writes in backticks exists

## Description

A document that names a module, a function or a file the code no longer has misleads its reader, and F0051's moves showed how fast such names go stale. This story adds a name check to the document check: in `README.md`, the operator guide and the project guide, every backticked dotted name that starts with `factory.` must be an importable module or an attribute of one, and every backticked repository path must exist. A relative Markdown link to a file must point to a file that exists, read from the document's folder (the human, 2026-11-05); a link to a web address or to a heading alone (`#...`) is not checked here. A placeholder in angle brackets (`<instance>`), a glob (`*`), a path under `/srv`, `/etc` or another absolute place, and a name inside a fenced code block are not checked. `docs/decisions.md` and `docs/runs/` are not read. Until S0004, the findings are only printed.

## Interface

- `factory.shared.domain.documents`: a frozen model `Reference(document: str, line: int, name: str, kind: Literal["module", "path", "link"])`; `named_references(document: str, text: str, top_level: frozenset[str]) -> list[Reference]` (pure), which finds the backticked names and paths of one document with their line numbers, and `unresolved(references: list[Reference], exists: Callable[[Reference], bool]) -> list[str]`, which gives one finding per reference that `exists` refuses, as `<document>:<line>: <name> does not exist`. A relative link's target is a `Reference` of kind `link` too, resolved against the document's folder (`../` included), with the part after a `#` left off.
- A backticked text is a path when it contains `/`, has no whitespace, does not start with `/` or `~`, holds no `://`, and either its first segment is in `top_level` (the checkout's top-level entries, passed by the command) or its last segment has a file extension. A dotted name is a module reference only when it starts with `factory.`.
- The command `factory.entry.check_documents` fills in `document` (the path relative to the checkout) and `top_level`, and gives `exists` its real meaning: a module or attribute found by `importlib`, a path found under the checkout. It reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`.
- A section headed `## Replaced from v1` or `## Replaced in v1.2` is not checked; it ends at the next `##` heading.
- Tests: `tests/shared/domain/test_document_references.py` (the pure functions) and `tests/entry/test_check_documents_references.py` (the command over a temporary checkout).

## Acceptance criteria

1. `named_references` finds `factory.a.b`, `factory.a.b.C.method` and a repository path such as `operator/vm/setup.sh` in backticks, with their lines; `claude/agents/reviewer.md` with `top_level` lacking `claude` is a path; it leaves out a placeholder in angle brackets, a glob, an absolute path (`/srv/factory`, `/etc/...`), `origin/main`, `os.path`, and anything inside a fenced block (one row per case). A link target with a `#fragment` (`[x](a.md#h)`) is the reference `a.md`.
2. A document that names a missing module, a missing attribute or a missing path, or links to a missing file (`[x](../../src/factory/nothing.py)`), gets one finding each; `[x](a.md#h)` with `a.md` missing is one finding; `../` is resolved from the document's folder (`docs/project-guide/`); a link to `https://...` or to `#a-heading` gets none, in the form of the Interface; existing ones get none (rows of one test).
3. `docs/decisions.md`, `docs/runs/` and the two *Replaced* sections give no finding, whatever they name; a missing name after a *Replaced* section's end (the next `##` heading) is reported.
4. The command prints the findings after today's findings of the document check, and its exit status does not change for them until S0004; it reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`, shown by one planted missing name in each.
5. `make check` stays green.
6. docs: `docs/project-guide/shared.md`, *The document check*: the name check. `docs/operator-guide/pipeline.md`: none. `docs/decisions.md`: none (the feature's decisions go in at S0004).

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "does not exist"
```
Expect: a number alone (the count of findings, possibly `0`)

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface does not define `Reference`. `unresolved(references, exists)` must print `<document>:<line>: <name> does not exist`, but `named_references(text)` takes only the text, so no document name enters. Which fields does `Reference` have (name, line, kind: module / path / link, document)? Who sets the document: `named_references` gets a `document` argument, or the command fills it in? I would choose a frozen model `Reference(document, line, name, kind)` and `named_references(document, text)`.
   2. "A repository path" is undefined. What makes a backticked string a path to check: a slash plus a file extension, a first segment that is a top-level folder of the checkout, or something else? Without a rule, `a/b` in prose, a command such as `make lint`, or a name such as `src/factory/...` give two coders different results. I would choose: contains `/`, has no whitespace, and its first segment is a top-level entry of the checkout (the check is done by the command, so `named_references` needs that rule written in the Interface).
   3. Criterion 1 lists only four cases for `named_references`. Rows are missing for a module name that does not start with `factory.` (not checked), a path under `/srv` or `/etc` (named in the Description), and a link target with a `#fragment` (the Interface says the fragment is left off). I would add one row for each.
   4. Criterion 2 has no row for the link side with a `#` after a file (`[x](a.md#h)` resolves `a.md`; missing `a.md` is a finding), and none for the relative path resolved from the document's folder (`../` against `docs/project-guide/`). I would add both.
   5. The Interface sentence "A section headed `## Replaced from v1` or `## Replaced in v1.2` is not checked" has criterion 3, but not for where such a section ends (the next `##` heading). I would add that a finding after the section is reported again.
   6. The checked document set (`README.md`, the operator guide, the project guide) is in the Description only. Criterion 3 covers `docs/decisions.md` and `docs/runs/`, but nothing tests that the command reads the operator-guide and project-guide folders and `README.md`. I would add that to criterion 4's test in `tests/entry/test_check_documents_references.py`.

   Format check passed. Architecture (pure rules in `shared.domain.documents`, I/O in `entry`) and scope (within feature scope, S0001) are fine. The smoke test is runnable, but its `Expect: counted` holds for any output, even if the command crashes in a pipeline; I would make it `grep -c "does not exist"` exit 0 and print a number, e.g. `Expect:` the digits alone.
4. 2026-11-06 human: 1. Yes: a frozen model `Reference(document, line, name, kind)`, with `kind` one of module, path and link, and `named_references(document, text, top_level)`. The command fills in `document` (the path relative to the checkout) and `top_level` (point 2).
   2. A backticked text is a repository path when it contains `/`, has no whitespace, does not start with `/` or `~`, holds no `://`, and either its first segment is in `top_level` (a `frozenset[str]` of the checkout's top-level entries, which the command passes) or its last segment has a file extension. The second half catches a path whose first folder was renamed, such as `claude/agents/reviewer.md`. `origin/main` and `pkrahmer/kumpel-factory` are not paths. One row each in criterion 1: `operator/vm/setup.sh` (path), `claude/agents/reviewer.md` with `top_level` lacking `claude` (path), `origin/main` (not a path), `/srv/factory` (not a path).
   3. Yes to all three rows: `os.path` (not checked), a path under `/srv` or `/etc` (not checked), `[x](a.md#h)` (the link target is `a.md`).
   4. Yes to both rows: `[x](a.md#h)` with `a.md` missing is one finding; `../` is resolved from the document's folder (`docs/project-guide/`).
   5. Yes: a *Replaced* section ends at the next `##` heading, and a missing name after it is reported again.
   6. Yes: criterion 4's test also shows that the command reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`, with one planted missing name in each.
   Smoke test: yes, make it print the number of findings, with `Expect:` a number alone.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. I wrote exactly these, nothing of my own: the `Reference(document, line, name, kind)` model, `named_references(document, text, top_level)` and the path rule (point 1, 2) into the Interface; the extra rows in criterion 1 (`claude/agents/reviewer.md`, `origin/main`, `/srv/factory`, `os.path`, the `#fragment` link) from points 2 and 3; the rows in criterion 2 (`a.md#h` with `a.md` missing, `../` from the document's folder) from point 4; the end of a *Replaced* section at the next `##` in the Interface and criterion 3 (point 5); the three read locations in the Interface and criterion 4 (point 6); the smoke test now prints the finding count, with `Expect:` a number alone.
   - Interface: names concrete modules and signatures (`factory.shared.domain.documents`, `factory.entry.check_documents`); it changes only `src` and tests, so the route is tests, not docs-only.
   - Criteria: each is testable by a test function, and each rule has its failing side (missing module, attribute, path or link; exempt places; a name after a *Replaced* section is reported again).
   - Smoke test: runnable (`grep -c` prints a number); the `Expect:` can be checked against the output. The command uses no pytest.
   - Architecture: the pure rules in `shared.domain`, the I/O (`importlib`, filesystem, `top_level`) in `entry`, as CLAUDE.md asks.
   - Scope: within the feature's S0001; `docs/decisions.md` and `docs/runs/` are excluded, as the feature's "Out of scope" says.
7. factory: started tests as vm.
