---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 268
comments_read: [6270411276]
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-19T15:18:36.193377Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T14:54:30.790338Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T14:54:30.797525Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T14:54:58.770383Z'
  stage: intake
  run: e2ca4484ff484362a2916a6277480492
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T14:55:19.416080Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T15:00:00.485885Z'
  stage: tests
  run: 46c8b62a088d4384ad2232594f5e525b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T15:00:21.640651Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-19T15:03:28.681848Z'
  stage: doing
  run: 83a82119910244929a394682a97f06c0
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-19T15:04:46.438750Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-19T15:05:04.338543Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-19T15:05:22.679392Z'
  stage: doing
  run: af99403547124ba0bf719c2c12ed5ea1
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-19T15:05:44.274238Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-19T15:07:30.313745Z'
  stage: tests
  run: 61fe1a6d000f4569a5804517c601c285
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-19T15:07:51.420280Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-19T15:09:58.251342Z'
  stage: doing
  run: 3ca6ba23dfd948ebb0b92e49fb7fe100
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-19T15:10:18.664732Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-19T15:11:43.614635Z'
  stage: review
  run: f8a370417bb64d1284b1019bd311c979
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-19T15:12:04.334127Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-19T15:12:25.777726Z'
  stage: doing
  run: 0afba8f5936245a9af5cf416f68410db
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-19T15:12:46.006892Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-19T15:14:41.346278Z'
  stage: tests
  run: 2087952f11584bb68d23a036a4f97963
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-19T15:15:01.857962Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-19T15:17:15.679045Z'
  stage: doing
  run: b0ced1fc55974ea58605c5a412242c24
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-19T15:17:36.151136Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-10-19T15:18:15.735270Z'
  stage: review
  run: 39bf2f0f293f4fdbac8718f3ed6e8e95
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-19T15:18:36.193377Z'
  stage: docs
---

# A stage's project command whose passed result is known for the same key is not run again

## Description

After a stage's agent the factory runs every check and report of the stage, even when it ran the same command on the same input minutes before. The docs stage's `check` on the coder's unchanged code is the plain case. This story keeps the result of every check and report a stage runs in a record of its own, `records/known-results.jsonl` in the state directory, under a key: the command, the tree it reads (`work_tree_id` without the command's `not_read`, S0001), a digest of the pipeline definition and the image. When the last run under the same key passed, the factory does not run the command again. It returns that result, marked as reused, and the journal line names the run it took: `` `check`: check: green (not run again: passed on tree 0123456789ab at 2026-10-18T15:20:01Z) ``. The reuse is a record too, with the time of the run it took, so no check is silenced and the count of runs on one tree is a query over the records. A failed or timed-out result is never reused, and a later failed run of the same key ends the reuse of an earlier pass. A changed read file, a merge of `main` that brings one, a changed pipeline definition and a new image each give a new key. When the key cannot be computed or the records cannot be read, the command runs as today, and the factory log says why. The preflight's probe, `ProjectCommands` and its implementations, and `project-commands.jsonl` (every real run) stay as they are. factory-rf's own `not_read` is the human's change after this story.

## Interface

`factory.domain.known_results` (`domain`, new):

```python
DefinitionDigest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class ResultKey(BaseModel):
    """What a command's result depends on: the command, its tree, the definition, the image."""

    command: CommandName
    tree: TreeId
    definition: DefinitionDigest
    image: str | None


class ResultRecord(BaseModel):
    """One run of a stage's project command under its key, or one reuse of an earlier passed run."""

    key: ResultKey
    at: UtcDatetime
    status: CheckStatus
    last_line: str
    duration_seconds: Duration
    reused: UtcDatetime | None = None


def definition_digest(definition: PipelineDefinition) -> DefinitionDigest: ...
def known_result(records: Sequence[ResultRecord], key: ResultKey) -> ResultRecord | None: ...
```

- Both models are frozen and forbid unknown keys. `ResultRecord` refuses `reused` that is not `None` unless `status` is `passed`.
- `definition_digest` is the SHA-256, in lower-case hex, of `definition.model_dump_json()` encoded as UTF-8: two loads of one text give the same digest, and a change of any value gives another.
- `known_result`: of the records whose `reused` is `None` and whose `key` equals `key`, the last in sequence order, when its status is `passed`; `None` when there is none or the last one failed or reached its time limit. Records with `reused` set are never a known result.

`factory.domain.checks` (`domain`):

```python
class ReusedRun(BaseModel):
    """The earlier run whose passed result a command took instead of running: its tree and start."""

    tree: TreeId
    at: UtcDatetime


class CheckResult(BaseModel):
    ...
    reused: ReusedRun | None = None


def command_line(result: CheckResult) -> str: ...
```

- `CheckResult` refuses `reused` that is not `None` unless `status` is `passed` (beside its rule on `exit_status`).
- `command_line` is `` `<command>`: <last_line> ``. For a reused result it is followed by ` (not run again: passed on tree <the first 12 characters of the tree> at <at as %Y-%m-%dT%H:%M:%SZ>)`.

`factory.application.boundaries` (`application`):

- `Boundaries` gains `result_records: RecordLog[ResultRecord] | None = None`, last (after F0020-S0007's `waiter`; the class is keyword-only).

`factory.application.known_results` (`application`, new):

```python
class KnownResults:
    """A stage's project commands: a passed result known for the same key is not run again."""

    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def run(self, command: str) -> CheckResult: ...
```

- The time limit of `command` is `definition.project_commands[command].time_limit` minutes, as `StageFinisher` takes it today.
- Without `boundaries.result_records` (`None`): `boundaries.project_commands.run(command, time_limit=...)`, its result returned unchanged; nothing is read or written and `git` is not called.
- Otherwise the key is built before the command starts: `ResultKey(command=command, tree=git.work_tree_id(definition.project_commands[command].not_read), definition=definition_digest(definition), image=<boundaries.settings.image, or None without settings>)`.
- A `GitError` of `work_tree_id`: the factory log gets `known results: no key for <command>: <error>`, the command runs, its result is returned and nothing is recorded.
- An `OSError` of `result_records.read()`: the factory log gets `known results: cannot read the records: <error>`, and the command runs and is recorded as when nothing is known.
- A known result (`known_result(records, key)` is not `None`): `project_commands.run` is not called. The result is `CheckResult(command=command, status="passed", exit_status=0, duration=timedelta(0), last_line=<known.last_line>, output_tail="", targets=[], reused=ReusedRun(tree=key.tree, at=known.at))`. The record appended is `ResultRecord(key=key, at=<clock now>, status="passed", last_line=<known.last_line>, duration_seconds=0, reused=known.at)`.
- No known result: `at` is the clock before the run, then `project_commands.run(command, time_limit=...)`. The record appended is `ResultRecord(key=key, at=at, status=result.status, last_line=result.last_line, duration_seconds=result.duration.total_seconds())`, and the result is returned unchanged. A `ProjectCommandError` or `ValueError` of the run propagates and nothing is recorded.
- An `OSError` of the append: the factory log gets `known results: cannot write the record of <command>: <error>`, and the result is still returned.

`factory.application.stage` (`application`):

- `StageFinisher` builds one `KnownResults(boundaries, definition)` and runs every check and report through it, in the same order and with the same rule: the first red check stalls the stage, rule 5, with the same stall detail.
- Each line the entry gets for a green check or a report is `command_line(result)`; `_with_command_lines` uses it, so a result that is not reused gives the line it gives today.

`factory.entry.wiring` (`entry`):

- `build_boundaries` gives `result_records=JsonLinesRecordLog(<state directory>/records/known-results.jsonl, ResultRecord)`.

Unchanged: `ProjectCommands`, `MakeProjectCommands`, `RecordingProjectCommands` and `project-commands.jsonl` (a reuse is no run and adds no line there), the preflight's probe and its stamp, `CommandRecord`, the stall reasons.

Tests (the tester writes them): `tests/domain/test_known_results.py`, `tests/domain/test_command_line.py`, `tests/application/test_known_results.py` (the `boundaries`, `checkout`, `human`, `clock` fixtures of `tests/conftest.py`, `RecordingCommands` of `tests/application/test_preflight_run.py` as `tests/application/test_recording_project_commands.py` uses it, `UnwritableRecordLog` of `tests/record_support.py`; boundaries with records built as `dataclasses.replace(boundaries, project_commands=..., result_records=JsonLinesRecordLog(tmp_path / "state" / "records" / "known-results.jsonl", ResultRecord))`), `tests/application/test_stage_known_results.py` (`open_story`, `stage_makefile`, `completed`, `WORK_ITEM`, `PATH`, `INSTANCE` and `ENVIRONMENT` of `tests/stage_run_support.py`, `ScriptedRun` of the fake agent runtime, `StageRunner` with a definition of its own), `tests/entry/test_wiring_known_results.py`. A `GitError` of `work_tree_id` comes from a subclass of `GitCli` that overrides that one operation, as `UnresolvableGit` in `tests/application/test_recording_project_commands.py` does for `resolve`. Changed under the feature's decision 15, by the tester only, nothing else in that module: `tests/domain/test_checks.py`, the test `test_fields_are_exactly_the_generic_seven`, renamed `test_fields_are_exactly_the_generic_eight`, whose expected set gains `"reused"`. It keeps what it checks.

## Acceptance criteria

1. `definition_digest` (rows of one parametrized test): two parses of `PIPELINE_YAML` give the same digest, 64 lower-case hex characters. A text with `check`'s `time_limit` 11, one with `check: {time_limit: 10, not_read: ["docs/*"]}` and one with the coder's `lease_duration` 70 each give a digest of their own. The digest equals `hashlib.sha256(definition.model_dump_json().encode("utf-8")).hexdigest()`.
2. The models (rows of one parametrized test, through a variable typed `type[BaseModel]`): `ResultRecord` with `reused` set and status `passed` is accepted. With `reused` set and status `failed` or `time_limit` it is refused. A `definition` of 63 or 65 characters or with upper-case hex is refused, one of 64 accepted. A `duration_seconds` of -1 is refused, 0 accepted. `CheckResult` with `reused` and status `passed` (exit status 0) is accepted, and with `reused` and status `failed` (exit status 2) or `time_limit` (exit status `None`) refused.
3. `known_result` (rows of one parametrized test, keys built from `"a" * 40` trees and `"b" * 64` digests): `[]` gives `None`. One passed run of the key gives it. A passed run, then a failed run of the key, gives `None`; a failed run, then a passed one, gives the passed one. A passed run, then a reuse of it, gives the run. A passed run of another command, another tree, another digest or another image gives `None` (four rows). A time-limited run as the last gives `None`. A reuse record of the key alone gives `None`.
4. `command_line` (rows of one parametrized test): a result of `check` with the last line `12 passed` gives `` `check`: 12 passed ``. The same result with `reused=ReusedRun(tree="a" * 40, at=2026-10-12T12:00:00.250000Z)` gives `` `check`: 12 passed (not run again: passed on tree aaaaaaaaaaaa at 2026-10-12T12:00:00Z) ``.
5. `KnownResults` without `result_records`: two runs of `check` call the project commands twice with the definition's time limit (10 minutes), return each inner result unchanged, write no `known-results.jsonl`, and do not call `work_tree_id` (a `GitCli` subclass that counts its calls of `work_tree_id` counts none).
6. `KnownResults` with records, the first run of `check` on the `checkout` (with `not_read: ["docs/*"]`): the project commands are called once, with the definition's time limit (10 minutes), their answer advancing the clock by one minute, and the inner result comes back unchanged. One record is written with the key `check`, `work_tree_id(["docs/*"])` of the checkout, `definition_digest` of the definition and image `None`, the clock's time before the run (not the advanced one), the inner result's status, last line and seconds, and `reused` `None`.
7. A second run on the same input, the clock advanced by 5 minutes: the project commands are not called again. The result is passed with exit status 0, a duration of 0, the first run's last line, an empty `output_tail`, no targets and `reused` `ReusedRun(tree=<the key's tree>, at=<the first record's at>)`. A second record holds the same key, the advanced time, `passed`, the same last line, `duration_seconds` 0 and `reused` the first record's `at`.
8. What gives a new key and what does not (rows of one parametrized test, between a first run and a second one of `check` with `not_read: ["docs/*"]`): an edit of `docs/guide.md` gives a reuse. An edit of `src/a.py` gives a run. A commit on `main` of only `docs/news.md`, fetched and merged into the checkout's branch, gives a reuse; one of `src/b.py` gives a run. A second `KnownResults` with a definition whose `lint` time limit differs gives a run. Boundaries whose `settings.image` is `img-2` after a first run with `img-1` give a run. A first run that failed (exit 2) or reached its time limit gives a run. A second run of `lint` on the same tree gives a run. In each row "a run" means the project commands are called a second time and the second record's `reused` is `None`, and "a reuse" means they are not, and it is the first record's `at`.
9. The faults (rows of one parametrized test): a `GitCli` subclass whose `work_tree_id` raises `GitError` makes `run("check")` call the project commands, return the inner result, write no record, and log one line starting `known results: no key for check: `. A records log whose `append` raises `OSError("disk full")` (`UnwritableRecordLog`) returns the inner result and logs `known results: cannot write the record of check: disk full`. A records log whose `read` raises `OSError("unreadable")` runs the command, appends its record, and logs `known results: cannot read the records: unreadable`.
10. A `ProjectCommandError` and a `ValueError` of the inner run each propagate out of `run("check")`, and no record is written (rows of one parametrized test).
11. The stage (rows of one parametrized test, through `StageRunner.run` three times on a story opened at `doing` with the roles `coder`, `reviewer` and `documenter`). The coder writes `src/a.py` and ends with `review`; the reviewer ends with `docs`; the documenter writes `docs/guide.md` and ends with `smoke-test`. The Makefile is `stage_makefile` whose recipes also append a line to a log outside the checkout. With `check: {time_limit: 10, not_read: ["docs/*", "factory/features/*"]}`: `check` ran once (one line in the log), and the documenter's entry ends with `` `check`: check done (not run again: passed on tree <the first 12 characters of the first record's tree> at 2026-10-12T12:00:00Z) ``. In a fourth row, with the `not_read` above and the doing stage's `reports: [test]`, the doing stage writes the record of `check` and then that of `test`, both with `reused` `None`, and the coder's entry ends with `` `check`: check done `` and `` `test`: test done ``. In two more rows, `check` ran twice: with `check: {time_limit: 10}` (no `not_read`), and with the `not_read` above plus a commit of `src/b.py` on `main` (`human.push_file`, then `boundaries.git.fetch()`) before the docs stage, which the docs stage's start merges into the branch. In both, the documenter's entry ends with `` `check`: check done ``.
12. A red `check` at the doing stage (the Makefile's `check` exits 2) stalls the work item as today: rule 5, the stall reason `check_red`, the stall detail `` `check` `` and its tail. A record with status `failed` is written. The next run of the doing stage on the same code (the coder writes the same `src/a.py`) runs `check` again: two lines in the log.
13. `build_boundaries`: `result_records` is a `JsonLinesRecordLog` whose `append` of a `ResultRecord` writes `<state directory>/records/known-results.jsonl`, and `project_commands` is still the `RecordingProjectCommands` it was.
14. `make check` stays green.
15. docs: `docs/operator-guide.md`, *What a stage run shows*, point 3: the line of a reused result, with an example, and that the command did not run. *The records*: a new subsection *The known results* for `records/known-results.jsonl`: one line per run and per reuse of a stage's check or report, its fields (`key` with `command`, `tree`, `definition`, `image`; `at`, `status`, `last_line`, `duration_seconds`, `reused`). What invalidates a known result: a read file changed, a merge of `main` bringing one, any change of the pipeline definition, a new image. That a failed result is never reused and the last run of a key decides. That deleting the file forgets every known result. The factory log's three lines. The command that counts the `check` runs of each tree, the most-run first:

    ```bash
    python3 -c "import json,collections as c; print(c.Counter(r['key']['tree'] for r in map(json.loads, open('/state/records/known-results.jsonl')) if r['key']['command']=='check' and r['reused'] is None).most_common())"
    ```

    *The pipeline definition*: what `not_read` is for (the paths a command does not read, left out of its key), replacing S0001's note that it does nothing yet, with this example, which factory-rf's own definition takes after this story: `check: {time_limit: 15, not_read: ["README.md", "docs/*.md", "factory/features/*.md", "factory/features/*.jsonl", "factory/stops.jsonl", "planning/*", "session-logs/*"]}`, and why only Markdown and JSON Lines files: `make lint` reads every Python file of the tree, wherever it lies. The warning that a project whose `check` scans changed files for secrets keeps a scan of the left-out files: factory-rf's docs stage will run `secrets` as a check of its own, with nothing left out. A command whose result depends on anything outside the tree and the image, such as dependencies fetched at run time with unpinned versions, is reused safely only when those versions are pinned in the tree (for example by a lockfile); otherwise leave `not_read` empty and do not rely on reuse for it. `docs/project-guide/processes-and-checks.md`, *Project commands*: `KnownResults`, `ResultKey`, `ResultRecord`, `definition_digest`, `known_result`, `ReusedRun`, `command_line`, `Boundaries.result_records`. `docs/project-guide/stages.md`, *The stage protocol*: where `StageFinisher` uses them. `docs/project-guide/watching.md`, *Boundaries*: the optional `result_records` (the log of the known results, see *Project commands*). `docs/project-guide/README.md`, *The files*: `processes-and-checks.md` also names `factory.application.known_results` and `factory.domain.known_results`. `docs/decisions.md`: an entry *A known result is not checked again*, dated with the story, with these reasons and rejected alternatives: the key is what the command reads, not the commit (the checks run before the stage's commit, and every commit carries a new journal entry) and not the stage (a docs stage's `check` on the coder's code is the same input); a list of what is left out, not a positive list of read paths (a forgotten path costs one run, never a silenced check); a failed result is never reused and the last run of a key decides (a flaky test is not hidden by an earlier pass); a store of its own in the state directory, not new fields on `CommandRecord` (no agent can write there, and `RecordingProjectCommands` sees no key); only the factory's own runs are known (an agent's own `make check` would be the agent's word).

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q --initial-branch=main "$d/w"
mkdir -p "$d/w/src" "$d/w/docs"
printf 'a\n' > "$d/w/src/a.py"
printf 'guide\n' > "$d/w/docs/guide.md"
printf 'check:\n\t@echo run >> ../ran\n\t@echo "check: green"\n' > "$d/w/Makefile"
uv run -q python - "$d" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.clock import SystemClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.git_cli import GitCli
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.boundaries import Boundaries
from factory.application.known_results import KnownResults
from factory.domain.known_results import ResultRecord

d = Path(sys.argv[1])
w = d / "w"
clock = SystemClock()
records = JsonLinesRecordLog(d / "known-results.jsonl", ResultRecord)
unused = None
boundaries = Boundaries(git=GitCli(w), hosting=unused, agent_runtime=unused, project_commands=MakeProjectCommands(w), work_item_reader=unused, work_item_writer=unused, cost_reader=unused, cost_writer=unused, pipeline_reader=unused, agent_definitions=unused, clock=clock, log=TimestampedFactoryLog(d / "factory.log", clock), health=unused, checkout=w, result_records=records)
text = 'contract: "1.0"\nproject_commands:\n  check: {time_limit: 1, not_read: ["docs/*"]}\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [done], checks: [check]}\n  done: {}\n'
known = KnownResults(boundaries, RuamelPipelineDefinitionReader().parse(text))
first = known.run("check")
second = known.run("check")
(w / "docs" / "guide.md").write_text("changed\n", encoding="utf-8")
third = known.run("check")
(w / "src" / "a.py").write_text("b\n", encoding="utf-8")
fourth = known.run("check")
saved = records.read()
print(first.last_line, first.reused is None)
print(second.last_line, second.reused is not None and second.reused.at == saved[0].at)
print(third.reused is not None, fourth.reused is None)
print(len((d / "ran").read_text(encoding="utf-8").splitlines()), [record.reused is None for record in saved])
EOF
```
Expect: four lines, `check: green True`, `check: green True`, `True True`, `2 [True, False, False, True]`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.known_results`, `factory.domain.checks`, `factory.application.boundaries`, `factory.application.known_results`, `factory.application.stage`, `factory.entry.wiring`). Every comment-stated behaviour has a criterion: the digest rule (1), the `reused`-only-on-passed rules (2), the `known_result` ordering and the skipping of reuse records (3), the `command_line` format (4), the no-records path (5), the key and the clock (6), the result and record of a reuse (7), the three faults and the error propagation (9, 10), the stage line and order (11, 12), the wiring (13).
   - Criteria: each fits one test function (the parametrized ones are rows of one test). Both sides are covered: the failing side of each model rule in 2, failed and time-limited last runs in 3, 8 and 12, a run for a changed key and a reuse for an unchanged one in 8 and 11, the fault paths in 9 and 10. `not_read` appears with and without in 8 and 11. The decision 15 change to `test_fields_are_exactly_the_generic_seven` is named and carries the feature's authority.
   - Smoke test: runnable. `GitCli.work_tree_id` already copes with a repository that has no index or commit yet (`src/factory/adapters/git_cli.py:419`). Its `Expect:` line is checkable and consistent with the script (the Makefile appends two lines to `ran`; the records are `[True, False, False, True]`).
   - Architecture: domain holds the pure models and rules, application holds `KnownResults` and the optional `Boundaries.result_records`, entry wires the `JsonLinesRecordLog`. Git is reached only through `Git.work_tree_id`, and `ProjectCommands` and its implementations stay unchanged. This matches `CLAUDE.md`.
   - Scope: every item is in the feature's Scope list. Nothing touches its "Out of scope" (agents' own checks, the preflight probe, the template and demos, pruning, counters). S0001's `TreeId` and `work_tree_id` are already in the tree. The two `CLAUDE.md` edits are the human's change 2, not this story's.
4. factory: started tests as self.
5. tester: I wrote the tests for every acceptance criterion. They are red on purpose: they fail for the right reason, and `make lint` is green.

   Criterion → test:
   - criterion 1: tests/domain/test_known_results.py::test_the_definition_digest_changes_with_every_value_and_only_then
   - criterion 2: tests/domain/test_known_results.py::test_a_reused_result_is_only_a_passed_one_and_the_key_holds_a_sha256_digest
   - criterion 3: tests/domain/test_known_results.py::test_the_known_result_is_the_last_run_of_the_key_when_it_passed
   - criterion 4: tests/domain/test_command_line.py::test_the_command_line_names_the_run_a_reused_result_took
   - criterion 5: tests/application/test_known_results.py::test_without_records_every_run_reaches_the_project_commands_and_no_key_is_built
   - criterion 6: tests/application/test_known_results.py::test_a_first_run_is_recorded_under_its_key_at_the_time_before_it
   - criterion 7: tests/application/test_known_results.py::test_a_second_run_on_the_same_input_takes_the_known_result
   - criterion 8: tests/application/test_known_results.py::test_only_a_change_of_what_the_command_reads_gives_a_new_key
   - criterion 9: tests/application/test_known_results.py::test_a_fault_of_the_key_or_the_records_runs_the_command_and_is_logged
   - criterion 10: tests/application/test_known_results.py::test_an_error_of_the_inner_run_propagates_and_records_nothing
   - criterion 11: tests/application/test_stage_known_results.py::test_the_docs_stage_takes_the_coders_passed_check_on_the_same_code
   - criterion 12: tests/application/test_stage_known_results.py::test_a_red_check_stalls_and_is_run_again_on_the_same_code
   - criterion 13: tests/entry/test_wiring_known_results.py::test_the_built_known_results_are_written_to_the_state_directory
   - criteria 14 and 15: no test; the checks and the docs stage cover them.

   Files created:
   - tests/domain/test_known_results.py
   - tests/domain/test_command_line.py
   - tests/application/test_known_results.py
   - tests/application/test_stage_known_results.py
   - tests/entry/test_wiring_known_results.py

   Earlier test file changed, under the feature's decision 15 as the Interface names it: in tests/domain/test_checks.py I renamed `test_fields_are_exactly_the_generic_seven` to `test_fields_are_exactly_the_generic_eight` and added `"reused"` to its expected set. Nothing else in that module changed.

   Test helpers, all kept inside the new modules:
   - In tests/application/test_known_results.py:
     - `CountingGit` and `KeylessGit` are `GitCli` subclasses that each override only `work_tree_id`.
     - `UnreadableRecordLog` raises `OSError("unreadable")` on `read` and appends to the real JSON Lines log, so the record of criterion 9 can be read back.
     - `RecordingCommands` is imported from `tests/application/test_preflight_run.py`, as the Interface says.
   - In tests/application/test_stage_known_results.py: the Makefile's recipes append `$@` to `tmp_path/ran.log`, outside the checkout.

   How the tests fail in the one run of `make test`:
   - Five modules could not be imported, because `factory.domain.known_results`, `factory.application.known_results` and `factory.domain.checks.ReusedRun`/`command_line` do not exist yet: tests/application/test_known_results.py, tests/application/test_stage_known_results.py, tests/domain/test_command_line.py, tests/domain/test_known_results.py and tests/entry/test_wiring_known_results.py.
   - `test_fields_are_exactly_the_generic_eight` fails because `CheckResult` has no `reused` field yet.

   The type check was skipped, as the stage allows. No question is open.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_wiring_known_results.py - ImportError while importing ...
6. factory: started doing as self.
7. coder: I built the story to its Interface. One test assertion can't pass against the stall note, which the story leaves unchanged. So `make check` is red only at that test, and I stopped there.

   Built:
   - `src/factory/domain/known_results.py` (new): `DefinitionDigest`, `ResultKey`, `ResultRecord` (`reused` only on `passed`), `definition_digest`, `known_result`.
   - `src/factory/domain/checks.py`: `ReusedRun`, `CheckResult.reused` (refused unless `passed`, in the existing validator), `command_line`.
   - `src/factory/application/known_results.py` (new): `KnownResults` with the key, the reuse, and the three fault paths and their log lines, as the Interface lists them.
   - `src/factory/application/boundaries.py`: `result_records`, last.
   - `src/factory/application/stage.py`: `StageFinisher` runs checks and reports through one `KnownResults`. `_run_command` is gone. `_with_command_lines` uses `command_line`.
   - `src/factory/entry/wiring.py`: `records/known-results.jsonl`.

   Main choice: `KnownResults` builds the definition digest once, in its constructor. I rejected computing it on every `run`, because the definition does not change during the life of the object. The refactor pass found nothing to change.

   `make check`: lint, types, layers, sast, secrets and licenses are green. In `make test` only one test fails:

   `tests/application/test_stage_known_results.py::test_a_red_check_stalls_and_is_run_again_on_the_same_code`
   ```
   tests/application/test_stage_known_results.py:178: in test_a_red_check_stalls_and_is_run_again_on_the_same_code
       assert "`check`\n" in note.body
   E   AssertionError: assert '`check`\n' in 'Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick.\n\n```text\ncheck done\nmake: *** [Makefile:11: check] Error 2\n```\n\n<!-- factory -->...'
   ```

   The stall detail is still `` `check` `` followed by the tail, exactly as criterion 12 says. `stall_note` (`src/factory/domain/post_texts.py:52`) has always put the detail's first line into the sentence (`` ...: `check`. Retrying... ``) and the rest into a fenced block. So the posted note never contains `` `check` `` followed by a newline, before or after this story. Criterion 12 also says the stall stays "as today", so changing the note is out of scope.

   Question: how should this test change?
   - (a) Assert `` "`check`." in note.body `` (or `` stall_note("check_red", 1, 2, detail=...) ``, as `tests/application/test_stalls.py:459` does) together with the existing `"check done"` check. This checks the same thing against the note as it is rendered.
   - (b) Read the stall detail from the journal or the stall result rather than from the posted note.
   - (c) Change `stall_note`. I advise against this: it is outside the story's scope.

   I would choose (a). If you agree, I will end with `tests` and name this change for the tester. I could not run the rest of that test separately, because my temporary probe was refused. Its other assertions (one `failed` record, then a second run of `check`) follow from `known_result` ignoring a failed last run.

   Noticed but not touched: `KnownResults._append` repeats the comment "the record is telemetry" from `RecordingProjectCommands.run`. The two cases mean the same thing, so I left both.
8. 2026-10-19 human: (a). The tester asserts `"`check`." in note.body` together with the existing `"check done"` check (or compares with `stall_note("check_red", 1, 2, detail=...)`, as `tests/application/test_stalls.py:459` does). This story's own test; `stall_note` stays as it is. End with `tests` naming the change.
9. factory: started doing as self.
10. coder: Following the human's answer (a) in entry 8, I made no code change. The tester needs to make one change to `tests/application/test_stage_known_results.py::test_a_red_check_stalls_and_is_run_again_on_the_same_code` (line 178). Replace `assert "`check`\n" in note.body` with `assert "`check`." in note.body`, or compare against `stall_note("check_red", 1, 2, detail=...)` as `tests/application/test_stalls.py:459` does. Keep the `"check done"` assertion. `stall_note` stays as it is.

    The implementation from entry 7 is already committed on the branch and unchanged:
    - `src/factory/domain/known_results.py`
    - `src/factory/domain/checks.py`
    - `src/factory/application/known_results.py`
    - `src/factory/application/boundaries.py`
    - `src/factory/application/stage.py`
    - `src/factory/entry/wiring.py`

    Its main choice is also unchanged: the digest is computed once, in the `KnownResults` constructor, rather than on every `run`.

    `make check` was not run in this round, since nothing changed. In entry 7, that test was the only red result in `make check`. Once the tester has changed it, the next doing round runs `make check` again.

    Noticed but not touched: as entry 7 says, the comment "the record is telemetry" appears in both `KnownResults._append` and `RecordingProjectCommands.run`.
11. factory: started tests as self.
12. tester: I made the one test change the human approved in entry 8 (option a), which the coder named in entry 10.

    Changed: in tests/application/test_stage_known_results.py::test_a_red_check_stalls_and_is_run_again_on_the_same_code (line 178), I replaced `assert "`check`\n" in note.body` with `assert "`check`." in note.body`. The reason: `stall_note` puts the detail's first line into its sentence (`...: `check`. Retrying...`), so a backtick-check-backtick followed by a newline never appears in the posted note. The `"check done"` assertion and the rest of the test are unchanged, and `stall_note` stays as it is.

    The criterion → test mapping from entry 5 still holds. I created no new file. Every module imports now that the implementation exists.

    `make test`: test: green (43.0 s), total coverage 99.08 %.

    `lint`: lint: green (0.0 s)
    `test`: test: green (47.8 s)
13. factory: started doing as self.
14. coder: The tester's change from entry 12 is on the branch, and `make check` is now green with no code change in this round: `check: green`, `test: green (41.9 s)`, total coverage 99.08 %.

    Built (committed in entry 7, unchanged since):
    - `src/factory/domain/known_results.py` (new): `DefinitionDigest`, `ResultKey`, `ResultRecord` (refuses `reused` unless the status is `passed`), `definition_digest`, `known_result`.
    - `src/factory/domain/checks.py`: `ReusedRun`, `CheckResult.reused` (refused unless `passed`, inside the existing validator), `command_line`.
    - `src/factory/application/known_results.py` (new): `KnownResults`. It builds the key, takes a known passed result, records each run and each reuse, and handles the three faults with their log lines.
    - `src/factory/application/boundaries.py`: `result_records`, added as the last field.
    - `src/factory/application/stage.py`: `StageFinisher` runs every check and report through one `KnownResults`. `_run_command` is removed, and `_with_command_lines` uses `command_line`.
    - `src/factory/entry/wiring.py`: `records/known-results.jsonl` in the state directory.

    Main choice: `KnownResults` computes the definition digest once, in its constructor. I rejected computing it on every `run`, because the definition does not change while the object exists.

    Refactor pass: I read the whole diff against `main` again and found nothing to change. None of the changed models is in `factory.domain.contract.CONTRACT` (`CheckResult` and `ResultRecord` are not), so no schema needed regenerating.

    What the journal changed: only one test assertion in the stall test (the human's answer (a) in entry 8, made by the tester in entry 12). The meaning of the task is the same, so I left `## Description` as it is.

    Noticed but not touched: the comment "the record is telemetry" appears in both `KnownResults._append` and `RecordingProjectCommands.run`. The two cases mean the same thing, so I kept both.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
15. factory: started review as self.
16. reviewer: 1. `tests/application/test_known_results.py:62` (`_raising`): this is a second copy of `_raising` in `tests/application/test_recording_project_commands.py:45`, with the same signature and body. Fix: the tester moves that helper to one shared module under `tests/`, using the standing leave to move a shared test helper, and both modules import it from there.
    2. `tests/application/test_known_results.py:116` (`Rig.log_lines`): this copies `log_lines` of `tests/log_support.py:6`, which reads the same `tmp_path / "state" / "factory.log"` the same way. Only the stripping of the time stamp is new. Fix: build it on `log_support.log_lines(tmp_path)` and keep only the stripping of the stamp, then drop `Rig.log_path`.

    Everything outside these two copies checked out:
    - Each of criteria 1 to 13 has a test that tests it.
    - The stated limits are tested on both sides:
      - `definition` with 63, 64 and 65 characters, and with upper-case hex.
      - `duration_seconds` at -1 and at 0.
      - `reused` with `passed`, `failed` and `time_limit`, on both models.
      - The failed and time-limited last run.
      - Without records, and without settings, where the `boundaries` fixture has none, so the image is `None`.
      - The three faults and the two errors that propagate.
    - The factory's `make check` after the coder was green (entry 14).
    - `src/` matches the Interface. The layers hold: the domain has no I/O, `KnownResults` stays in `application` and reaches git only through `Git.work_tree_id`, and `wiring` is the only place it is wired.
    - No secrets, no check-silencing markers, and no strings handed to a shell.
    - None of the five new findings of `make duplicates` is in a module this story changed.

    Earlier tests:
    - `tests/domain/test_checks.py` (M): changed under the human's leave, which is the story's Interface naming `test_fields_are_exactly_the_generic_seven` → `test_fields_are_exactly_the_generic_eight` under the feature's decision 15. The change is only the rename and `"reused"` added to the expected set, which is within that leave.
17. factory: started doing as self.
18. coder: Both findings in the reviewer's entry 16 are test changes, so I changed no code this round. The tester makes these two changes:

    1. Move `_raising` to one shared module under `tests/`, under the standing leave to move a shared test helper. It is defined twice now, with the same signature and body: in `tests/application/test_known_results.py:62` and in `tests/application/test_recording_project_commands.py:45`. After the move both modules import it from the shared place. Every earlier test keeps its name and what it checks, and the entry names `tests/application/test_recording_project_commands.py` as the earlier file changed.
    2. In this story's own `tests/application/test_known_results.py:116`, build `Rig.log_lines` on `log_lines(tmp_path)` from `tests/log_support.py`. Keep only the stripping of the time stamp, and drop `Rig.log_path`.

    The implementation is unchanged since entry 7 and is already committed on the branch:
    - `src/factory/domain/known_results.py`
    - `src/factory/domain/checks.py`
    - `src/factory/application/known_results.py`
    - `src/factory/application/boundaries.py`
    - `src/factory/application/stage.py`
    - `src/factory/entry/wiring.py`

    Main choice, also unchanged: the definition digest is computed once, in the `KnownResults` constructor. I rejected computing it on every `run`, because the definition does not change while the object exists.

    I did not run `make check` in this round because nothing changed. It was last green in entry 14.

    What the journal changed: only the tests, so `## Description` stays as it is.

    Noticed but not touched: the comment "the record is telemetry" appears in both `KnownResults._append` and `RecordingProjectCommands.run`.
19. factory: started tests as self.
20. tester: I made the two test changes the coder named in entry 18. They come from the reviewer's findings in entry 16.

    1. Moved the shared helper, under the standing leave in `CLAUDE.md` to move a shared test helper. `_raising` was defined twice, with the same signature and body: in `tests/application/test_known_results.py` and in `tests/application/test_recording_project_commands.py`. It now lives once, as `raising`, in the new module `tests/project_command_support.py`, and both test modules import it from there. The earlier test file I changed is `tests/application/test_recording_project_commands.py`: only the local definition is removed and the import is added. Every test in it keeps its name and checks the same thing.
       - Not moved: `tests/application/test_preflight_run.py` has its own `_raising`. Its parameter has a different type (`ProjectCommandError`), and entry 18 did not name it.
    2. In this story's `tests/application/test_known_results.py`, `Rig.log_lines` is now built on `log_support.log_lines(tmp_path)` and keeps only the stripping of the time stamp. `Rig.log_path` is dropped. `Rig` now holds `tmp_path`, and `_rig` passes it in.

    The criterion → test mapping from entry 5 still holds. Every module imports, because the implementation exists.

    Created: `tests/project_command_support.py`.
    Changed: `tests/application/test_known_results.py` and `tests/application/test_recording_project_commands.py`.

    `make lint`: lint: green (0.0 s)
    `make test`: test: green (41.5 s), total coverage 99.08 %.

    `lint`: lint: green (0.0 s)
    `test`: test: green (42.4 s)
21. factory: started doing as self.
22. coder: The tester's changes from entry 20 are on the branch, and `make check` is green with no code change this round: `check: green`, `test: green (48.5 s)`, total coverage 99.08 %. Both of the reviewer's findings in entry 16 were test-side copies, and entry 20 fixed them:
    - `raising` is now shared in `tests/project_command_support.py`.
    - `Rig.log_lines` is now built on `tests/log_support.py`.

    What I built, unchanged since entry 7 and already committed:
    - `src/factory/domain/known_results.py`
    - `src/factory/domain/checks.py`
    - `src/factory/application/known_results.py`
    - `src/factory/application/boundaries.py`
    - `src/factory/application/stage.py`
    - `src/factory/entry/wiring.py`

    Main choice: `KnownResults` computes the definition digest once, in its constructor. I rejected computing it on every `run`, because the definition does not change while the object exists.

    Refactor: there was no new diff of mine to re-read this round, so I changed nothing.

    What the journal changed: only tests, so `## Description` stays as it is.

    Noticed but not touched:
    - The comment "the record is telemetry" appears in both `KnownResults._append` and `RecordingProjectCommands.run`.
    - `tests/application/test_preflight_run.py` keeps its own `_raising`, typed for `ProjectCommandError`. Entry 20 left it out on purpose.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
23. factory: started review as self.
24. reviewer: no findings

    What I checked, for round 1:
    - Both findings from entry 16 are fixed. `raising` now lives only in `tests/project_command_support.py`, and both `tests/application/test_known_results.py:27` and `tests/application/test_recording_project_commands.py:22` import it from there. `Rig.log_lines` (`tests/application/test_known_results.py:111`) is built on `log_support.log_lines` and only strips the time stamp; `Rig.log_path` is gone. `UnreadableRecordLog` has no counterpart in `tests/record_support.py`: `UnwritableRecordLog` fails on `append`, not on `read`.
    - Criteria 1 to 13 each have a test that checks what the criterion says. These are rows of parametrized tests where the criterion asks for rows. Stated limits are tested on both sides: a digest of 63, 64 and 65 characters and in upper-case hex; `duration_seconds` at -1 and 0; `reused` with `passed`, `failed` and `time_limit` on both models; a failed and a time-limited last run; runs with and without records; and the three faults and the two errors that propagate. The factory's `make check` after the coder was green (entry 22).
    - `src/` matches the Interface: `factory.domain.known_results`, `ReusedRun`/`CheckResult.reused`/`command_line` in `factory.domain.checks`, `KnownResults` in `factory.application.known_results`, `Boundaries.result_records` last, `StageFinisher` running checks and reports through one `KnownResults`, and the wiring of `records/known-results.jsonl`. The layers hold: the domain does no I/O, git is reached only through `Git.work_tree_id`, and only `entry.wiring` wires. No secrets, no markers that silence a check, no strings built into a shell command. Neither changed model is in `CONTRACT`, so no schema needed regenerating.
    - Work item: the journal states the main choice (the digest is computed once, in the constructor) and the alternative it rejected. The Description matches what was built. The docs criterion still describes what the reader needs to know.

    Earlier tests:
    - `tests/domain/test_checks.py` (M): human's leave. The Interface names the rename `test_fields_are_exactly_the_generic_seven` → `test_fields_are_exactly_the_generic_eight` and the added `"reused"`, under the feature's decision 15. The diff makes only that change.
    - `tests/application/test_recording_project_commands.py` (M): standing leave to move a shared test helper. The only change is that the local `_raising` is removed and `raising` is imported from `tests/project_command_support.py`. Every test keeps its name and still checks the same thing.
25. factory: started docs as self.
