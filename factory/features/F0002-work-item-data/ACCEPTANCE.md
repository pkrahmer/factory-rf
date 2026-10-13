---
stage: accept
pr: 36
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0002-S0001, F0002-S0002, F0002-S0003, F0002-S0004, F0002-S0005, F0002-S0006, F0002-S0007, F0002-S0008]
---
# Acceptance of Work item data

## Verdict

**accepted with drafts.** Every goal and scope item of `FEATURE.md` has a story, and the feature demo ran green against the real entry points: draft, check, start, edit, write back, restore, then the cost sidecar. `make check` is green. Two findings are worth stories, and neither is a broken promise. First, the journal and the form check read a code fence differently: one entry whose text leaves a fence open makes the form check report a valid work item as damaged (section 4). Second, the documentation has stale and story-bound sentences, and its example for the one command exits 2 on this repository (section 5).

## 1 Scope

None. I compared each scope item with the archived stories and the code they name:

- identifiers, paths and order: S0001, `factory.domain.identifiers`, `factory.domain.paths`
- the state in the front matter: S0002, `factory.domain.work_item`
- one reader and one writer: S0003, `factory.adapters.work_item_markdown` behind `factory.application.files`
- sections: S0004, `factory.domain.sections`
- the journal and its restore: S0005, `factory.domain.journal`
- the story form check: S0006, `factory.domain.story_form`
- the cost-record sidecar: S0007, `factory.domain.cost_records`, `factory.adapters.cost_records_jsonl`
- the command: S0008, `factory.entry.check_story`, `factory.entry.wiring`

Each clause of the Goal's "done when" is shown by the demo in section 2. No story strays into Out of scope: when records are written, bills, pipeline definition and hand-over are all left to F0003, F0005 and F0009.

One observation, not a gap. `WorkItemReader.read(path)` is `parse` only, so reading a backlog file as a specification means reading the text yourself and calling `parse_specification`. The command does this in its own `_read_text` (`src/factory/entry/check_story.py:45`), which repeats the reader's `cannot read` mapping in a second wording. The factory reads files through git as text, so `parse_specification(text)` is likely the main path anyway. I am leaving this for F0005 to judge when it opens a story.

## 2 Feature demo

This is the walk a user of the feature takes. A human writes a draft in a v1.1 tree and checks it with the command; the factory starts it and journals it; the story is edited and written back; an agent's tampering is undone; two runs leave cost records. Run from the repository root; it creates files only under a temporary directory. My first two attempts failed because of my script, not the code: I called `read(path)` on a backlog file, and I appended a spec edit after the last journal entry, where it belongs to the journal. Both behaviours are as the Interfaces say. This is the third run:

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

print("4. Edit and write back; speaker and kind are read as data")
back = reader.read(path)
edited = append_entry(back, NewEntry(speaker="tester", kind="result", text="tests written\nall red"))
edited = edited.model_copy(update={"body": insert_paragraph(edited.body, "Assignment", "Note from the human.")})
writer.write(path, edited)
again = reader.read(path)
print("  equal after write and read:", again == edited)
print("  last factory record:", last_record(again, speaker="factory"))
print("  last result:", last_record(again, kind="result"), "| text:", repr(entry_text(again, 3)))
forged = again.model_copy(update={"body": again.body.replace("3. tester:", "3. human:")})
print("  speaker forged in the text; last human record:", last_record(forged, speaker="human"))

print("5. An agent tampers with state and journal and edits the spec; the restore puts state and journal back")
tampered = again.model_copy(update={"state": again.state.model_copy(update={"stage": "done"}),
                                    "body": again.body.replace("tests written", "approved!").replace("Print a greeting.", "Print a loud greeting.")})
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
4. Edit and write back; speaker and kind are read as data
  equal after write and read: True
  last factory record: number=2 speaker='factory' kind='started'
  last result: number=3 speaker='tester' kind='result' | text: 'tests written\nall red'
  speaker forged in the text; last human record: number=1 speaker='human' kind='created'
5. An agent tampers with state and journal and edits the spec; the restore puts state and journal back
  stage: tests | entry 3: 'tests written\nall red' | spec edit kept: True
  form findings after restore: []
6. Cost records: started, then completed by replacing its line; unknowns stay unknown
  sidecar: factory/features/F0009-greetings/in-progress/F0009-S0001-greet-the-user.costs.jsonl
    {"run":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","work_item":"F0009-S0001","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-13T09:00:00Z","duration_seconds":41.0,"end_reason":"completed","turns":7,"tokens":{"input":12,"output":3438,"cache_read":0,"cache_creation":0},"cost_usd":"0.3450","image":null}
    {"run":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","work_item":"F0009-S0001","stage":"tests","role":"tester","attempt":0,"status":"completed","started_at":"2026-10-13T09:00:00Z","duration_seconds":600.0,"end_reason":"time_limit","turns":null,"tokens":null,"cost_usd":null,"image":null}
  round trip equal: True | cost: Decimal('0.3450') | time_limit run cost, tokens, turns: None None None
  the sidecar is a work item: False
exit 0
```

Green. Each clause of the Goal shows in the output:

- read: step 3
- checked against the project's form: steps 1, 3 and 5
- edited and written back with its key order: steps 3 and 4
- journal read by speaker and kind, not from the text: step 4, where a speaker forged in the text changes no record
- a heading in a fence is no section: step 3, where `## start the server` is not listed
- cost records round-trip with unknowns kept unknown: step 6

`make check` was green as I found it: `check: green`, total coverage 99.64 %. The only F0002 line it misses is `src/factory/entry/check_story.py:131`, the `if __name__ == "__main__"` line, which a subprocess test exercises.

## 3 Mutation score

None: the project has no `make mutants` target. This is deliberate and recorded in `docs/decisions.md` ("No `mutants` target, no mutmut": over the whole package it could outgrow the lease). There is no score and there are no survivor groups.

The nearest evidence is the review history. Every rework round in this feature was a refused side the Interface stated but no test checked, which is what a mutant would have shown:

- S0004: fence runs shorter than three, an indented title, negative indices
- S0005: an indented entry number, trailing blank lines, a restore onto trailing blanks
- S0006: an indented or fenced criterion
- S0007: an infinite duration

All were closed with tests. In each case, by the reviewer's own account, a mutated line would have passed the earlier tests. S0004's fence run is the reviewer's own example: `{1,}` for `{3,}` passed every test.

## 4 What the stories noticed

1. **An unclosed fence in an entry's text desynchronises the journal from the form check.** This is the weightiest finding. S0005's coder noticed it (entries 4, 8 and 10) and the reviewer left it open "for a later story". It is documented as a known limit, but only as "hides later headings". Reproduced here: three entries are appended, the second with the text `red; output starts:` + a fence line + `E   assert 1 == 2`. `last_record` and `entry_text(doc, 3)` see three entries, but `check_story_form(..., folder="in-progress")` returns `the journal data lists 3 entries but the text shows 2`. The journal ends an entry at the next column-0 number whatever the fences; the form check counts only lines outside blocks. The operator guide tells the human that this finding means "the state is damaged, so restore the file". The form check is meant to run before and after every agent run (S0006's Assignment), and an agent's result often quotes output that a tail can cut mid-fence. Draft F0002-S0009.
2. An info string after a backtick fence may contain backticks, which CommonMark forbids. Noticed in S0004 by the coder (entries 4, 8 and 12) and the reviewer. A line such as ```` ```x`y ```` opens a block in `sections` but not in a CommonMark renderer. Low weight; no draft.
3. A paragraph passed to `insert_paragraph` with leading blank lines gets an extra blank line (S0004 reviewer). Not specified. Low weight; no draft.
4. The fault text `no front matter` is a literal in both `src/factory/adapters/work_item_markdown.py` and `src/factory/entry/check_story.py` (S0008 coder and reviewer). Tests catch a change on either side; a typed `NoFrontMatter` error or a shared constant would be cleaner. Low weight; no draft. The human may fold it into the first story that touches the reader.
5. The same UTC field validator (`value.astimezone(UTC)`) now exists in four copies: `domain/git.py` from F0001, plus `domain/hosting.py`, `domain/work_item.py` and `domain/cost_records.py`. The S0002 reviewer counted three before S0007 added the fourth. It follows the idiom, but a shared aware-UTC type is a candidate for a later clean-up. No draft.
6. Journal entries are counted outside code blocks although rule 6 of S0006's Interface does not say so (S0006 reviewer, carried to the human through entries 5 to 10 and never answered). The code and the guide agree with each other. Finding 1 is the case where this rule bites.
7. S0003's reviewer weighed and accepted the import of `pydantic_core.ErrorDetails`, a package that `pyproject.toml` does not list directly (pinned through pydantic). Listed under 6 for the human.

## 5 The documentation as a whole

I read it as a newcomer, from `README.md` down. Draft F0002-S0010 repairs the first five points; point 6 is left as it is.

1. `docs/project-guide.md:457` says of the work item reader and writer: "Wiring does not use them yet." S0008 wired the reader (`factory.entry.wiring.build_work_item_reader`), so this is stale.
2. Story-bound sentences in a guide meant to stay true: `docs/project-guide.md:403` ("The reader of the next story names a fault by that location") and `:544` ("This story is the format only").
3. The guide's "Errors" section lists every error type except `CostRecordFormatError`, which is described only under "Cost records".
4. The README's status sentence lists the work item data types, the journal, the reader and writer and the check command. It omits identifiers and paths, sections, the story form check and the cost records.
5. The operator guide's only example does not run here. It names `factory/features/F0002-work-item-data/backlog/F0002-S0008-the-story-check-command.md`, but this repository has no `backlog` folder and no `factory/story-form.md`. Run as written, it prints `cannot read factory/story-form.md: [Errno 2] No such file or directory: '/work/factory-rf/factory/story-form.md'` and exits 2; the story's real path under `done/` gives the same. The README points the newcomer at this command and at this guide. Nothing says that this repository's own `factory/` tree is v1's (`drafts/`, `ongoing/`, `FEATURE.md`, `TICKET.md`) and so is not what the command checks. The guide's sentence "`ongoing` is the pipeline's folder and is not accepted" describes v1's pipeline to a v1.1 operator. Behaviour and documentation agree; the example misleads.
6. No contradiction found between stories. The guide gives the reader's `cannot read: <reason>` and the command's `cannot read <path>: <reason>` as two different texts, and both are correct for their place. The fault tables, the notation example, the journal format and the form rules match the code. I re-ran the S0001 sorting example and the feature demo above against the guide's statements.

## 6 Decisions taken for the human

`FEATURE.md` lists 14 decisions, and I found nothing in the code that departs from them. These further ones were taken in the story logs:

1. `BRANCH_PREFIX` is defined in `factory.domain.identifiers` and re-exported by `paths`, not defined in `paths` as S0001's Interface said; the other way is an import cycle. The coder took this, the reviewer accepted it, and it is recorded in `docs/decisions.md`.
2. In S0004 the coder extended criteria 3, 7 and 16 during review rounds. The additions restate the Interface's own limits (three or more, column 0, `NonNegativeInt`), and no human saw them before merge. The S0004 reviewer judged that they do not change scope.
3. Journal entries are counted only outside code blocks (S0006, rule 6 silent). Raised for the human in S0006's entries 5 to 10 and not answered. Finding 4.1 depends on it.
4. The cost is checked by a before-validator on `CostRecord` that refuses an int, float or bool even from Python code (S0007 coder). The shared pydantic fault ranking moved to `src/factory/adapters/validation_faults.py`, which both readers use.
5. `duration_seconds` is finite, and the reader refuses `NaN`, `Infinity` and `-Infinity` as `not valid JSON`. The human decided this (S0007, entry 7, option A).
6. `main` of the check command reports a missing `feature.md` (S0008 criterion 23). The human approved this in S0008's entry 3.
7. `lifecycle_folder_of_location` is a public function beyond S0008's Interface; the reviewer accepted it.
8. `pydantic_core.ErrorDetails` is imported from a transitive dependency without declaring `pydantic-core` in `pyproject.toml` (S0003 reviewer judged it no new dependency). "New dependency" is on the not-without-asking list, so confirm or ask for the direct pin.
9. `STORY_FORM_FILE` is `factory/story-form.md` and `FEATURE_FILE_NAME` is `feature.md` (v1.1's glossary), while this repository's tree is v1's (`TICKET.md`, `FEATURE.md`). So `factory-check-story` cannot be used on factory-rf's own stories until the tree moves to v1.1. That is consistent with `CLAUDE.md`'s vocabulary rule, but it is worth a conscious yes.

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see 3), no image scan and no SBOM.

## 8 Cost

72 runs, 68.8 min, $17.45 for 8 stories; that is about $2.18 and 9 runs per story.

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

S0004 and S0005 stand out. Their logs say why: every rework round asked for a test of a limit the Interface stated but no criterion spelled out on its refused side. The code was never wrong, except for two private docstrings in S0005. Each such round cost one coder run that made no change, one tester run and one reviewer run.

The story writer can avoid that cost. Where an Interface states "three or more", "at column 0" or a `NonNegativeInt`, put its refused side into a criterion. `CLAUDE.md` already makes it a review finding.

## Proposed stories

- `drafts/F0002-S0009-journal-entries-close-their-code-fences.md`: an entry whose text leaves a fence open makes the form check report a valid work item as damaged and hides the sections after the journal; `render_entry` closes it (section 4, item 1).
- `drafts/F0002-S0010-documentation-after-work-item-data.md`: stale and story-bound sentences in the project guide, the missing error type, the README's status, and the operator guide's example that exits 2 on this repository (section 5).

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants n/a (no target, by decision)
   1 Scope: none. Every scope item and every clause of the Goal has a story and code. One observation: `WorkItemReader.read` is `parse` only, so the check command reads a backlog file's text itself and repeats the `cannot read` mapping in a second wording.
   2 Feature demo: green, exit 0. The walk goes draft, check (exit 1, then 0), start, write, check (`ok`), edit and write back (equal), journal read by speaker and kind (a speaker forged in the text changes no record), tamper and restore, then the cost sidecar (completed by replacing its line; the `time_limit` run's cost, tokens and turns read back as None). My first two attempts failed on my own script, not the code. `make check` was green as I found it, with 99.64 % coverage.
   3 Mutation score: no `make mutants` target (`docs/decisions.md`). Instead, every rework round in this feature was an untested refused side of a stated limit.
   4 Noticed: an entry whose text leaves a code fence open makes the form check report `journal data lists 3 entries but the text shows 2` on a valid work item, and hides the sections after the journal. I reproduced it; draft S0009. Low weight, no draft: backticks in a backtick info string, the `no front matter` literal shared by the adapter and the entry layer, four copies of the UTC validator, and journal entries counted only outside fences (never answered in S0006).
   5 Docs: the project guide still says "Wiring does not use them yet" for the reader, has two story-bound sentences, and lists no `CostRecordFormatError` under Errors. The README's status is behind. The operator guide's only example exits 2 here (`cannot read factory/story-form.md`), and the guide does not say that this repository's tree is v1's. Draft S0010.
   6 Decisions: FEATURE.md's 14 decisions, plus 9 from the logs: BRANCH_PREFIX moved to identifiers; criteria extended by the coder in S0004; journal entries counted outside fences; the cost before-validator; finite duration (decided by the human); the feature.md criterion (approved by the human); public `lifecycle_folder_of_location`; `pydantic_core` imported without a direct pin; v1.1 paths that do not match this repository's v1 tree.
   7 Slow checks: none offered.
   8 Cost: 72 runs, 68.8 min, $17.45. S0004 (14 runs) and S0005 (12) stand out: their rework rounds asked only for refused-side tests the criteria did not spell out, and the code was never wrong apart from two private docstrings.
