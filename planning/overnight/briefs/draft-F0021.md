# Brief: draft F0021, the factory records what the human did (a small feature built before F0020)

## Goal

Write the feature `F0021-the-factory-records-what-the-human-did` and its stories (two or three) so that v1.1 can build them before F0020. The aim (the human's word of 2026-10-18): measure how often a story needs the human, so that the factory can move from "an LLM on watch" to "runs alone"; give the status-map viewer (`planning/overnight/restructure-after-f0011.md`, "The status map") machine-readable data for it; and take two recurring questions off the human. Every new datum lives in the work item's front matter or in a JSON sidecar, never only in Markdown text: the viewer reads the front matter (YAML) and the sidecars (JSON lines) and never parses prose.

## Inputs (read these first)

- The journal and state: `src/factory/domain/journal.py` (`JournalKind`, `JournalRecord` with `number`, `speaker`, `kind`, `at`, `stage`, `run`; `NewEntry`), `src/factory/domain/work_item.py` (the state: `stage`, `blocked`, `round`, `attempts`, `crashes`), the handlers that append entries (`src/factory/application/handlers/`, `stage.py`, `stalls.py`, `recovery.py`), and their tests.
- The cost records: `src/factory/application/costs.py`, the sidecar `<work item>.costs.jsonl` (one JSON line per run), the cost table posted on the pull request, the bill at `done`, and the acceptance report (`src/factory/application/acceptance.py`, `acceptance_reading.py`).
- The stops: `src/factory/application/stops.py`, `machine.py`, the factory log in `/state/factory.log` (today the only record of a machine stop; the viewer cannot reach it).
- A real journal: `factory/features/F0019-the-write-guard-by-the-kernel/done/` (front matter and journals of S0004, with its questions, a merge conflict, a round cap, and of `F0019-A0001`, with two crashes from `mutants/seed`).
- The forms and rules: `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `claude/agents/*.md` (above all `reviewer.md` and `intake.md`), `CLAUDE.md`, `docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`.

## The content

1. **The cause on the record.** `JournalRecord` gains optional fields: for a `question` record, `blocked` (the block it opened: `question`, `round_cap`, `attempts_cap`, `crash_cap`, or whatever block values the code has); for a `stall` or `crash` record, `reason`, a short fixed value (find the causes the code already distinguishes, for example the time limit, a refused seal, a failed merge of main, no usable reply; name them in the Interface). Old records without the fields stay valid. A viewer can then compute, from the front matter alone: every wait for the human (from a `question` record's `at` to the next human `comment` record's `at`) with its cause, send-backs per stage, stalls and crashes with their reasons.
2. **The human's line in the cost table.** The cost table on the pull request and the acceptance report gain the count of human interventions: questions answered, by cause, and the hours the work item waited for the human. Computed from the records of point 1, not from text.
3. **Machine stops on GitHub.** A machine stop and its clearing are today only lines in `/state/factory.log`. Record them where the viewer can read them: recommend a place (for example a JSON-lines file on `main` such as `factory/stops.jsonl`, written when the stop clears with both times if the stop itself prevented a push, or the instance's own records) and give the choice as a decision for the human. A stop must never be lost because git was what failed.
4. **Room in the run record.** The sidecar line of a run stays additive: new fields are optional. Name in the feature that F0020 adds its spend-limit waits there, and add now what the runtime already knows per run: the tool calls the Claude Code hook refused (`permission_denials` of the result), as a count and the paths, so that F0019's decision 16 (the cross-check) becomes a count. The kernel's refusals are only text in a tool's output: say so, and do not parse them.
5. **Two texts (a separate, documents-sized story):**
   - `claude/agents/reviewer.md`: from round 2 on, findings that are only quality points in the story's own new tests (a copied helper, a name, a duplicate) go forward as recorded notes in the reviewer's entry, not back; findings on criteria, architecture, security or `src/` still send it back. And the leave: the reviewer may add an acceptance criterion that only pins behaviour already built and needs no code change, writing it into the work item and naming it in its entry, instead of asking the human (the tester writes the test).
   - `docs/operator-guide.md`: never edit a running work item on `main`; answer in the pull request; the agents amend the story on its branch (a human's edit on main conflicts with the branch at the next stage start, as F0019-S0004 showed).
   Pin both with tests of the shipped agent texts, as `tests/test_claude_agent_texts.py` does.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. Points 1 to 4 are one or two stories; point 5 is one.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small and generic (the human's rule: solid over clever): the engine learns no stage names, no reviewer groups and no agent's text; it records what it already decides.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0021-the-factory-records-what-the-human-did/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0021-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from a temporary folder outside the repository that holds a copy of the story laid out as `factory/features/F0021-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0021-the-factory-records-what-the-human-did/`. Do not start sub-agents. No paid model call of your own. Remove every temporary folder you create (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (where machine stops are recorded above all), what the viewer can compute from the new data, and anything you could not place.
