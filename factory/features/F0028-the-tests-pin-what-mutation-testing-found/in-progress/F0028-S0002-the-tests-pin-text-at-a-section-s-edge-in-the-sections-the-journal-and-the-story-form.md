---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 313
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T01:27:41.154801Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T01:26:59.736860Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T01:26:59.742643Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T01:27:19.968405Z'
  stage: intake
  run: 4fd899352ddf48b7acfa9f0ff62261ba
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T01:27:41.154801Z'
  stage: tests
---

# The tests pin text at a section's edge in the sections, the journal and the story form

## Description

The mutation sweep of 2026-10-19 found the same gap in three readers of a work item's Markdown: every test leaves a blank line between a `## ` heading and the first text under it, and none puts a numbered line right above a heading. So a reader that started one line late (missing the first line under the heading) or one line early (taking the line above the heading for part of the section) would pass. The readers are `section_text` of `factory.domain.sections`, the journal's `entry_text` of `factory.domain.journal` and the story form's numbered items of `factory.domain.story_form` (the acceptance criteria and the journal entries `check_story_form` counts). The sweep also found that no test has an empty fenced block, whose closing fence stands on the line right after the opening one. The sweep's line numbers of these modules are today's. This story pins these edges as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The sweep's `_item_text` survivor is not pinned: on today's code it is equivalent (decision 3 of `feature.md`).

## Interface

No module under `src/factory/` changes. The behaviour pinned (`domain`):

- `factory.domain.sections.section_text(body, heading)`: the text under the heading starts on the line right after it, whether or not a blank line stands between.
- `factory.domain.sections.code_blocks(lines)`: a closing fence on the line right after the opening one closes the block there.
- `factory.domain.journal.entry_text(document, number)`: entry 1 is found on the line right after `## Journal`, and a numbered line right above `## Journal` is never an entry.
- `factory.domain.story_form.check_story_form(document, form, folder=...)`: a criterion or a journal entry on the line right after its heading counts, and a numbered line right above `## Acceptance criteria` or `## Journal` is never a criterion or an entry.

Tests (the tester writes them): `tests/domain/test_section_edges.py` (the `sections` and `journal` rows) and `tests/domain/test_story_form_edges.py` (the story form rows). Their bodies are written out as literal texts, since `_body` of `tests/domain/test_story_form.py` always puts a blank line under a heading. Documents with a state are built with `initial_state("intake")` of `factory.domain.work_item`, and a started story's state as `_state` of `tests/domain/test_story_form.py` builds it (`WorkItemState(stage="done", journal=[JournalRecord(number=1, speaker="factory", kind="result")])`). No earlier test changes.

In criterion 4, `CRITERIA` is `1. It works.\n2. make check stays green.\n3. docs: none.` and `SMOKE` is `` ```bash\nuv run factory\n```\nExpect: it works. ``, the form is the `FORM` of `tests/domain/test_story_form.py` (`# Story form\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n`), and every body starts `# A story\n\n## Description\n\nText.\n\n## Interface\n\n`.

## Acceptance criteria

1. `section_text` at the heading's edge (rows of one parametrized test): `section_text("# T\n## A\nfirst\nsecond\n## B\n", "A")` is `"first\nsecond"`, and `section_text("# T\n\n## A\n\nfirst\nsecond\n\n## B\n", "A")` is `"first\nsecond"` as well.
2. An empty fenced block (rows of one parametrized test; `TICKS` is three backticks, as in `tests/domain/test_sections.py`): `code_blocks([TICKS, TICKS])` is `[CodeBlock(start=0, end=1)]`, and `code_blocks([TICKS, TICKS, "text", TICKS])` is `[CodeBlock(start=0, end=1), CodeBlock(start=3, end=None)]`.
3. The journal at its heading's edge (rows of one parametrized test, each a `WorkItemDocument(state=initial_state("intake"), body=<body>)`):
   - Body `# T\n\n## Journal\n1. 2026-10-12 human: created.\n2. intake: accepted.\n`: `entry_text(document, 1)` is `"created."` and `entry_text(document, 2)` is `"accepted."`.
   - Body `# T\n\n## Smoke test\n\n1. a numbered line\n## Journal\n\n1. 2026-10-12 human: created.\n`: `entry_text(document, 1)` is `"created."`, and `entry_text(document, 2)` raises `WorkItemFormatError` whose fault is `no journal entry 2`.
4. The story form at a section's edges (rows of one parametrized test; each row the body after the common start, the folder and the state):
   - `None.\n\n## Acceptance criteria\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n` (criterion 1 right under its heading), folder `backlog`, no state: `[]`.
   - `1. a numbered line\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n` (a numbered line right above the criteria), folder `backlog`, no state: `[]`.
   - `None.\n\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n1. a numbered line\n## Journal\n\n1. human: created.\n` (a numbered line right above the journal), folder `done`, the started state with one record: `[]`.
   - `None.\n\n## Acceptance criteria\n\n` + `CRITERIA` + `\n\n## Smoke test\n\n` + `SMOKE` + `\n\n## Journal\n1. human: created.\n` (entry 1 right under its heading), folder `done`, the started state with one record: `[]`; the same body in folder `backlog`, no state: exactly `[FormFinding(line=25, message="a backlog story carries no journal entries")]`.
5. `make check` stays green.
6. docs: none. `docs/project-guide/` already describes these readers and the story form check, and this story changes neither.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.journal import entry_text
from factory.domain.sections import code_blocks, section_text
from factory.domain.work_item import WorkItemDocument, initial_state

print(repr(section_text("# T\n## A\nfirst\nsecond\n## B\n", "A")))
print(code_blocks(["```", "```"]))
body = "# T\n\n## Smoke test\n\n1. a numbered line\n## Journal\n1. 2026-10-12 human: created.\n"
print(entry_text(WorkItemDocument(state=initial_state("intake"), body=body), 1))
EOF
```

Expect: three lines, `'first\nsecond'`, `[CodeBlock(start=0, end=1)]` and `created.`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: it names concrete functions in `factory.domain.sections`, `journal` and `story_form` (`section_text`, `code_blocks`, `entry_text`, `check_story_form`). It also names the test modules, the literal bodies and the state builders. No signature changes, and each comment states one behaviour.
   - Criteria: each is testable by one parametrized test with literal inputs and outputs. Each behaviour in the Interface has a criterion: text on the line after a heading, the empty fenced block, entry 1 right under `## Journal`, and a numbered line above a heading. Each rule has its failing side: entry 2 raises `WorkItemFormatError` with `no journal entry 2`, a numbered line above a heading yields no criterion or entry, and the backlog row yields the `FormFinding`. I counted lines for the `FormFinding(line=25, ...)` row: the common start is 8 lines, the entry lands on line 25, and `line` is `start + 1`.
   - Smoke test: the heredoc is runnable with `uv run -q python`. The `Expect:` line names three outputs that can be compared exactly.
   - Architecture: nothing under `src/` changes. The tests sit in `tests/domain/`, mirroring `factory.domain`, and the story follows the standing leave and tests-only rules in `CLAUDE.md`. It changes no earlier test.
   - Scope: it matches S0002 in `feature.md`. The `_item_text` survivor is left out as equivalent (decision 3), and no out-of-scope item is touched.
4. factory: started tests as self.
