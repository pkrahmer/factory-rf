---
stage: accept
pr: 39
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0002-S0001, F0002-S0002, F0002-S0003, F0002-S0004, F0002-S0005, F0002-S0006, F0002-S0007, F0002-S0008, F0002-S0009, F0002-S0010]
---
# Acceptance of Work item data

## Verdict

**accepted.** Every scope item and every clause of the Goal has a story and code. The feature demo against the real entry points is green, and that includes the case the first acceptance found broken: an entry that quotes output cut inside a code fence now leaves the form check clean. `make check` is green with 99.64 % coverage. The two drafts proposed by the first acceptance (S0009, S0010) are merged and did what they promised. What remains are low-weight observations, listed under 4 for the human. None of them is worth a story of its own.

## 1 Scope

None. This is the second acceptance of F0002. The first (pull request 36, merged) mapped every scope item to its story and code, and nothing under `src/` changed since then except S0009's `render_entry` and `opening_fence`:

- identifiers, paths and order: S0001, `factory.domain.identifiers`, `factory.domain.paths`
- the state in the front matter: S0002, `factory.domain.work_item`
- one reader and one writer: S0003, `factory.adapters.work_item_markdown` behind `factory.application.files`
- sections with code fences respected: S0004, `factory.domain.sections`, plus `opening_fence` from S0009
- the journal and its restore: S0005, `factory.domain.journal`. S0009 made it agree with the form check about fences, so entries stay in step with their records (SI1.1) and fences are respected (SI1.3).
- the story form check: S0006, `factory.domain.story_form`
- the cost-record sidecar: S0007, `factory.domain.cost_records`, `factory.adapters.cost_records_jsonl`
- the command `factory-check-story`: S0008, `factory.entry.check_story`, `factory.entry.wiring`
- the documentation repair: S0010, docs only

No story strays into Out of scope. The observation from the first acceptance still stands and is still not a gap: `WorkItemReader.read(path)` is `parse` only, so the check command reads a backlog file's text itself (`src/factory/entry/check_story.py`, `_read_text`) and maps `cannot read` in its own wording. F0005 will judge this when it reads stories through git.

## 2 Feature demo

This is the walk a user of the feature takes, run in a temporary v1.1-layout project:

1. A human writes a draft and checks it with the command.
2. The factory starts the story and journals it.
3. A tester's result quotes a tail of test output cut inside a code fence, which is the case S0009 repairs. The story is edited and written back, and its journal is read by speaker and kind.
4. An agent's tampering is undone.
5. Two runs leave cost records.

Run from the repository root:

```bash
uv run python - <<'EOF'
import subprocess, sys, tempfile
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.domain.agent_runs import TokenCounts
from factory.domain.cost_records import CostRecord
from factory.domain.identifiers import branch_name, parse_work_item_file_name, work_item_order
from factory.domain.journal import NewEntry, append_entry, entry_text, last_record, restore_state_and_journal
from factory.domain.paths import cost_records_path, folder_of, work_item_path
from factory.domain.sections import insert_paragraph, sections
from factory.domain.story_form import check_story_form
from factory.domain.work_item import initial_state

FENCE = "`" * 3
FORM = "# Story form\n\n## Assignment\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n"
DRAFT = ("# Greet the user\n\n## Assignment\n\nPrint a greeting.\n\n"
         "## Acceptance criteria\n\n1. It greets.\n2. make check stays green.\n3. docs: none.\n\n"
         f"## Smoke test\n\n{FENCE}bash\n## start the server\necho hi\n{FENCE}\nExpect: hi\n\n## Journal\n")

def cli(root, *paths):
    done = subprocess.run([sys.executable, "-m", "factory.entry.check_story", *paths], cwd=root, capture_output=True, text=True)
    print("  $ factory-check-story", *paths)
    for line in (done.stdout + done.stderr).splitlines():
        print("   ", line)
    print("    exit", done.returncode)

root = Path(tempfile.mkdtemp())
feature, name = "F0009-greetings", "F0009-S0001-greet-the-user.md"
(root / "factory/features" / feature / "backlog").mkdir(parents=True)
(root / "factory/features" / feature / "in-progress").mkdir()
(root / "factory/story-form.md").write_text(FORM)
(root / "factory/features" / feature / "feature.md").write_text("# Greetings\n")
draft_path = work_item_path(feature, "backlog", name)
(root / draft_path).write_text("---\nstage: done\n---\n" + DRAFT)

print("1. The human's draft, with front matter that tries to skip a stage, then without it")
cli(root, draft_path)
(root / draft_path).write_text(DRAFT)
cli(root, draft_path)

print("2. Identity and order")
ids = [parse_work_item_file_name(n).id for n in ["F0009-A0001.md", name, "F0009-S0002.md"]]
print("  order:", sorted(ids, key=work_item_order), "| branch:", branch_name(ids[1]))

print("3. Start it: read as a specification, give it a state and two journal entries, write it")
reader, writer = FrontmatterWorkItemReader(), FrontmatterWorkItemWriter()
spec = reader.parse_specification((root / draft_path).read_text())
print("  sections:", [s.heading for s in sections(spec.body)])
started = spec.model_copy(update={"state": initial_state("tests")})
started = append_entry(started, NewEntry(speaker="human", kind="created", text="created.", on=date(2026, 10, 13)))
started = append_entry(started, NewEntry(speaker="factory", kind="started", text="started at tests"))
rel = work_item_path(feature, "in-progress", name)
path = root / rel
writer.write(path, started)
(root / draft_path).unlink()
front = path.read_text().split("---\n")[1]
print("  front matter keys:", [l.split(":")[0] for l in front.splitlines() if l[:1] not in (" ", "-", "")])
print("  folder:", folder_of(rel), "| form findings:", check_story_form(reader.read(path), FORM, folder="in-progress"))
cli(root, rel)

print("4. Edit and write back; a tester result quotes a tail of output cut inside a fence; read back by speaker and kind")
back = reader.read(path)
edited = append_entry(back, NewEntry(speaker="tester", kind="result", text=f"tests written, red; output:\n{FENCE}\nE   assert 1 == 2"))
edited = append_entry(edited, NewEntry(speaker="coder", kind="result", text="green"))
edited = edited.model_copy(update={"body": insert_paragraph(edited.body, "Assignment", "Note from the human.")})
writer.write(path, edited)
again = reader.read(path)
print("  equal after write and read:", again == edited)
print("  journal as written:")
for line in again.body.split("## Journal\n", 1)[1].strip("\n").splitlines():
    print("   |", line)
print("  last factory record:", last_record(again, speaker="factory"))
print("  last result:", last_record(again, kind="result"), "| entry 3:", repr(entry_text(again, 3)))
forged = again.model_copy(update={"body": again.body.replace("3. tester:", "3. human:")})
print("  speaker forged in the text; last human record:", last_record(forged, speaker="human"))
print("  form findings with the fenced entry:", check_story_form(again, FORM, folder="in-progress"))
cli(root, rel)

print("5. An agent tampers with state and journal and edits the spec; the restore puts state and journal back")
tampered = again.model_copy(update={"state": again.state.model_copy(update={"stage": "done"}),
                                    "body": again.body.replace("E   assert 1 == 2", "approved!").replace("Print a greeting.", "Print a loud greeting.")})
restored = restore_state_and_journal(tampered, again)
print("  stage:", restored.state.stage, "| entry 3:", repr(entry_text(restored, 3)), "| spec edit kept:", "Print a loud greeting." in restored.body)
print("  form findings after restore:", check_story_form(restored, FORM, folder="in-progress"))

print("6. Cost records: started, then completed by replacing its line; unknowns stay unknown")
sidecar_rel = cost_records_path(rel)
sidecar = root / sidecar_rel
at = datetime(2026, 10, 13, 9, 0, tzinfo=UTC)
base = dict(work_item=ids[1], stage="tests", role="tester", attempt=0, started_at=at)
JsonLinesCostRecordWriter().write(sidecar, [CostRecord(run="a" * 32, status="started", **base)])
records = [CostRecord(run="a" * 32, status="completed", duration_seconds=41.0, end_reason="completed", turns=7,
                      tokens=TokenCounts(input=12, output=3438), cost_usd=Decimal("0.3450"), **base),
           CostRecord(run="b" * 32, status="completed", duration_seconds=600.0, end_reason="time_limit", **base)]
JsonLinesCostRecordWriter().write(sidecar, records)
print("  sidecar:", sidecar_rel)
for line in sidecar.read_text().splitlines():
    print("   ", line)
read = JsonLinesCostRecordReader().read(sidecar)
print("  round trip equal:", read == records, "| cost:", repr(read[0].cost_usd),
      "| time_limit run cost, tokens, turns:", read[1].cost_usd, read[1].tokens, read[1].turns)
print("  the sidecar is a work item:", folder_of(sidecar_rel) is not None)
EOF
echo "exit $?"
```

```
1. The human's draft, with front matter that tries to skip a stage, then without it
  $ factory-check-story factory/features/F0009-greetings/backlog/F0009-S0001-greet-the-user.md
    factory/features/F0009-greetings/backlog/F0009-S0001-greet-the-user.md: a backlog story carries no front matter: stage
    exit 1
  $ factory-check-story factory/features/F0009-greetings/backlog/F0009-S0001-greet-the-user.md
    factory/features/F0009-greetings/backlog/F0009-S0001-greet-the-user.md: ok
    exit 0
2. Identity and order
  order: ['F0009-S0001', 'F0009-S0002', 'F0009-A0001'] | branch: work-item/F0009-S0001
3. Start it: read as a specification, give it a state and two journal entries, write it
  sections: ['Assignment', 'Acceptance criteria', 'Smoke test', 'Journal']
  front matter keys: ['stage', 'blocked', 'round', 'attempts', 'crashes', 'pull_request', 'comments_read', 'handed_over', 'claim', 'journal']
  folder: in-progress | form findings: []
  $ factory-check-story factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.md
    factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.md: ok
    exit 0
4. Edit and write back; a tester result quotes a tail of output cut inside a fence; read back by speaker and kind
  equal after write and read: True
  journal as written:
   | 1. 2026-10-13 human: created.
   | 2. factory: started at tests
   | 3. tester: tests written, red; output:
   |    ```
   |    E   assert 1 == 2
   |    ```
   | 4. coder: green
  last factory record: number=2 speaker='factory' kind='started'
  last result: number=4 speaker='coder' kind='result' | entry 3: 'tests written, red; output:\n```\nE   assert 1 == 2\n```'
  speaker forged in the text; last human record: number=1 speaker='human' kind='created'
  form findings with the fenced entry: []
  $ factory-check-story factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.md
    factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.md: ok
    exit 0
5. An agent tampers with state and journal and edits the spec; the restore puts state and journal back
  stage: tests | entry 3: 'tests written, red; output:\n```\nE   assert 1 == 2\n```' | spec edit kept: True
  form findings after restore: []
6. Cost records: started, then completed by replacing its line; unknowns stay unknown
  sidecar: factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.costs.jsonl
    {"run":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","work_item":"F0009-S0001","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-13T09:00:00Z","duration_seconds":41.0,"end_reason":"completed","turns":7,"tokens":{"input":12,"output":3438,"cache_read":0,"cache_creation":0},"cost_usd":"0.3450","image":null}
    {"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0009-S0001","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-13T09:00:00Z","duration_seconds":600.0,"end_reason":"time_limit","turns":null,"tokens":null,"cost_usd":null,"image":null}
  round trip equal: True | cost: Decimal('0.3450') | time_limit run cost, tokens, turns: None None None
  the sidecar is a work item: False
exit 0
```

Green, exit 0. Each clause of the Goal shows in the output:

- read: step 3
- checked against the project's form: steps 1, 3, 4 and 5, by the domain function and by the command
- edited and written back with its key order: steps 3 and 4
- journal read by speaker and kind, not from the text: step 4, where a speaker forged in the text changes no record
- a heading inside a code fence is never a section: step 3 (`## start the server` is not listed). Step 4 shows that an entry quoting an open fence gets its closing line, so the form check and the command both stay clean and see all four entries.
- cost records round-trip with unknown cost and tokens kept unknown: step 6

Beyond the demo, I probed `render_entry` on nested and mixed fences: a four-backtick block holding three backticks, a `~~~` block holding three backticks, a closing run longer than the opening, and a fence on the numbered line followed by a later `py` fence. Each got exactly one closing line with the opening run, or none where none was due.

`make check` was green as I found it: `check: green`, total coverage 99.64 %. The only F0002 line it misses is `src/factory/entry/check_story.py:131`, the `if __name__ == "__main__"` guard, which a subprocess test runs.

## 3 Mutation score

None to report: the project has no `make mutants` target. That is a recorded decision (`docs/decisions.md`, "No `mutants` target, no mutmut"), so there is no score and there are no survivor groups.

The nearest evidence is still the review history. Rework rounds in S0004 to S0007 were each a refused side of a stated limit that no test covered, which a mutant would have shown, and all were closed with tests. S0009 had no rework round. Its tester covered the limits the Interface states on both sides without a criterion asking for it: three backticks against two (`"``x"` gives None), the two-digit indent, and a closed block against an open one.

## 4 What the stories noticed

The items from the first acceptance that were not drafted are all still in the code, verified today. S0009 added one new item.

1. **A test name is half true** (new; S0009's tester, coder and reviewer). `tests/domain/test_journal.py:208` is `test_entry_text_returns_the_text_as_it_was_given`, but since S0009 `entry_text` returns the text as rendered, closing line included. The test still passes because its text has no fence. Renaming it is a test change, so it belongs to the tester of the next story that touches `test_journal.py`. No draft.
2. The fault text `no front matter` appears twice: in `src/factory/adapters/work_item_markdown.py:111` and as `_NO_FRONT_MATTER` in `src/factory/entry/check_story.py:27`. Tests catch a drift on either side. No draft. It fits the first story that touches the reader, likely in F0005.
3. The UTC field validator `value.astimezone(UTC)` exists in four copies: `domain/git.py:76`, `domain/hosting.py:87`, `domain/work_item.py:35` and `domain/cost_records.py:48`. A shared aware-UTC annotated type would replace them, but that crosses F0001 and F0002 modules. No draft; it is a candidate for a later clean-up.
4. In `sections`, a backtick fence's info string may itself contain backticks, which CommonMark forbids (S0004). Low weight, no draft.
5. A paragraph passed to `insert_paragraph` with leading blank lines gets an extra blank line (S0004 reviewer). This is unspecified. Low weight, no draft.
6. The unreachable `fence is None` guard in `journal._closing_line` (S0009) narrows the type for mypy, where an `assert` would trip bandit. It is accepted and needs nothing.

The weighty item of the first acceptance, an open fence that desynchronised the journal from the form check, is fixed (S0009) and shown fixed in section 2.

## 5 The documentation as a whole

None. I read `README.md`, `docs/operator-guide.md`, the F0002 sections of `docs/project-guide.md` and `docs/decisions.md` from the top, as a newcomer:

- Each of the five repairs S0010 promised is in place: the wiring sentence, no story-bound sentences in "The state" and "Cost records", `CostRecordFormatError` and `NothingToCommit` under "Errors", the README's status, and the operator guide's statement of the v1.1 layout and of this repository's v1 tree.
- S0009's documentation matches the code. The journal format gives the closing line, `entry_text` is "as rendered", the known limit is gone, `opening_fence` is in the sections table, and a decision entry gives the two rejected alternatives.
- Every runnable example in the project guide prints what the guide says. I re-ran all seven blocks under "Identity, order and places", "The data of a work item", "Reading and writing", "Cost records", "Sections" and "The form check".
- The operator guide's two outcomes hold. Run here, the command exits 2 with `cannot read factory/story-form.md: ...`. In a temporary v1.1-layout project, the placeholder path prints `factory/features/F0001-example/backlog/F0001-S0001-example-story.md: ok` and exits 0.
- The guides do not contradict each other. The form check's "an unclosed block hides a later `## Journal`" is about the human's specification text. The journal can no longer produce such a block.

Two remarks, too small for a story:

- The operator guide's opening paragraph lists the built parts (git, build commands, `claude -p`, the hosting-service client) without the work item data. The next sentence does name `factory-check-story`.
- The README's status sentence is now one long enumeration of every built part. As features accumulate, a short summary with a pointer to the project guide would read better. That is the documenter's call when the next feature lands.

## 6 Decisions taken for the human

`FEATURE.md` now lists 17 decisions. Three of them (15 to 17) settle what the first acceptance raised: journal entries are counted only outside blocks, with `render_entry` closing them; `pydantic_core.ErrorDetails` without a direct pin; and v1.1's file names stand. I found nothing in the code that departs from any of the 17.

You saw these log decisions in the first acceptance and accepted them by merging it. They stand unchanged:

- `BRANCH_PREFIX` lives in `identifiers` and is re-exported by `paths`. This is recorded in `docs/decisions.md`.
- The coder extended S0004's criteria 3, 7 and 16 with the Interface's own limits.
- The cost before-validator refuses int, float and bool even from Python code.
- `duration_seconds` is finite (your decision).
- A missing `feature.md` is a finding of the command (your approval).
- `lifecycle_folder_of_location` is public.

New from S0009 and S0010, taken without you:

1. S0009's `render_entry` decides on an open block by reading the rendered lines (number prefix and indent included), not the raw text, so it uses the same `code_blocks` reading as the form check. The coder made this choice and the reviewer accepted it. It follows from the story's rules.
2. S0009's tester added a case of exactly three backticks to criterion 9's table, for the three-against-two side.
3. S0010 ran as a documentation-only story through every stage. Its tester and coder had nothing to do by design, and its reviewer reviewed an empty diff. This is a process choice, not a product one. Whether doc-only drafts should take a shorter path is a question for the factory (see 8).

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see 3), no image scan and no SBOM.

## 8 Cost

84 runs, 75.6 min, $19.36 for 10 stories, about $1.94 and 8.4 runs per story.

| Story | Runs | Minutes | Cost | Rework rounds |
|---|---|---|---|---|
| S0001 | 6 | 5.9 | $1.45 | 0 |
| S0002 | 6 | 4.1 | $1.12 | 0 |
| S0003 | 6 | 7.1 | $2.07 | 0 |
| S0004 | 14 | 11.0 | $2.51 | 2 |
| S0005 | 12 | 11.8 | $3.07 | 2 |
| S0006 | 10 | 10.1 | $2.22 | 1 |
| S0007 | 11 | 11.6 | $3.01 | 1, with a question |
| S0008 | 7 | 7.2 | $2.00 | 0, with an intake question |
| S0009 | 6 | 3.9 | $1.36 | 0 |
| S0010 | 6 | 2.9 | $0.55 | 0 |

As the first acceptance found, S0004 and S0005 stand out. Their rework rounds asked only for refused-side tests that the criteria did not spell out.

The two late stories were the cheapest. S0009 had criteria that spelled out every failing side (the first acceptance's advice), and it went through without rework for $1.36. S0010 cost $0.55, but three of its six runs (tester, coder, reviewer) had nothing to work on by design, because the story was docs only. Small in money, it is still a pattern worth knowing: a documentation-only story pays for every stage of the pipeline.

The two acceptances cost $2.86 for the first, plus this one; neither is in the sum above.

## Proposed stories

None. No finding has the weight of a story. Items 4.1 to 4.3 are each a few lines and fit the first later story that touches the module (`test_journal.py`, the reader, the domain DTOs); I list them for you instead of drafting them.

## Log (append only)

1. acceptor: accepted; 0 drafts proposed; make mutants n/a (no target, by decision in docs/decisions.md)
      1 Scope: none. Every scope item and every clause of the Goal has a story and code. Since the first acceptance, S0009 is the only story that changed `src/`. The observation that the check command reads a backlog file's text itself (`_read_text`) still stands; it is not a gap, and F0005 will judge it.
      2 Feature demo: green, exit 0. In a temporary v1.1 project the walk goes: draft, check (exit 1, then 0), start, write, check (`ok`). A tester result quoting output cut inside a fence gets its closing line, and the form check and the command stay clean with all four entries seen. Then edit and write back (equal), speaker and kind read as data, tamper and restore, and the cost sidecar with unknowns kept unknown. Extra probes of nested and mixed fences in `render_entry` were correct. `make check` was green as I found it, with 99.64 % coverage.
      3 Mutation score: there is no `make mutants` target (recorded decision), so no score. S0009 had no rework round; its tests cover both sides of each limit.
      4 Noticed: one new item, the test name `test_entry_text_returns_the_text_as_it_was_given` (now half true after S0009). Still open from before: the `no front matter` literal in two layers, four copies of the UTC validator, backticks allowed in a backtick info string, and the extra blank line from `insert_paragraph`. All are low weight with no draft; each fits the next story that touches the module.
      5 Docs: none. All S0010 repairs and S0009's documentation are in place. All seven project-guide examples print what the guide says, and both operator-guide outcomes hold: exit 2 in this v1 tree, `ok` in a v1.1 tree. Two small remarks: the operator guide's opening list of built parts and the README's status sentence keep growing.
      6 Decisions: FEATURE.md's 17 decisions, with 15 to 17 settling the first acceptance's open points; the code departs from none of them. The six log decisions already accepted with the first acceptance are unchanged. New: `render_entry` reads the rendered lines rather than the raw text; the tester added a three-backtick case to criterion 9; S0010 ran docs-only through every stage.
      7 Slow checks: none offered.
      8 Cost: 84 runs, 75.6 min, $19.36. S0004 (14 runs) and S0005 (12) stand out, as before, because their criteria did not spell out refused-side tests. S0009 ($1.36) and S0010 ($0.55) were the cheapest. In S0010, three of six runs had nothing to do by design, because a docs-only story still pays for every stage.
