---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 276
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T18:12:01.772253Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T18:00:45.256223Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T18:00:45.266099Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T18:01:10.708776Z'
  stage: intake
  run: f315cee09690418c8aef836fdb35d7a2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T18:01:31.655014Z'
  stage: tests
- number: 5
  speaker: factory
  kind: crash
  at: '2026-10-19T18:04:50.733930Z'
  stage: tests
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T18:04:52.791487Z'
  stage: tests
- number: 7
  speaker: tester
  kind: result
  at: '2026-10-19T18:07:44.732964Z'
  stage: tests
  run: be605248478f4993be62cb16be58f09e
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T18:08:05.704565Z'
  stage: doing
- number: 9
  speaker: coder
  kind: result
  at: '2026-10-19T18:10:14.663404Z'
  stage: doing
  run: 79f605fd8e354d0ea1ef409bf5e14b9b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T18:10:35.423939Z'
  stage: review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-10-19T18:11:40.909102Z'
  stage: review
  run: 101e64f39884474e91e8f68bf2c99147
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T18:12:01.772253Z'
  stage: doing
---

# factory-watch's main hands its streams and its instance to the watch

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`factory-watch`'s `main` (`factory.entry.watch`) picks the output and error streams (the given ones, else `sys.stdout` and `sys.stderr`) and the boundaries and instance (the given pair, else both from the environment), then calls `run_watch`. No test runs `main` through to `run_watch`. The tests call it only for an option or a settings refusal, and the one test that would get past the settings, `test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout`, skips whenever `/work/checkout/.git` exists, as it does in every factory run. So F0026's mutation run left 14 mutants of `main` alive (writing to `None`, always to `sys.stdout`, taking the environment although boundaries were given, dropping the settings' instance, passing `None` as the error stream), and `watch.py` lines 82-83 and 87 uncovered. The text of the "origin/main does not resolve" `GitError`, which the operator reads, is not pinned either: `run_watch` and `Watcher` each kept two survivors that replace half of it with `None`. This story pins all of that with new tests and changes no code. `run_watch`, the board, the event line and the exit statuses stay as they are, and so do their tests.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of, as it is:

```python
# factory.entry.watch (entry)
def main(argv: Sequence[str] | None = None, *, boundaries: Boundaries | None = None, instance: Name | None = None, out: TextIO | None = None, err: TextIO | None = None) -> int: ...
def run_watch(boundaries: Boundaries, instance: Name, out: TextIO, err: TextIO) -> int: ...
# factory.application.watcher (application)
class Watcher:
    def evaluate(self, definition: PipelineDefinition) -> Event: ...
```

- With both `boundaries` and `instance` given, `main` does not read the environment, and runs the watch as `instance` on those boundaries.
- `main` writes the watch to `out` and its error line to `err`, and to `sys.stdout` and `sys.stderr` when `out` or `err` is left out.
- With `boundaries` or `instance` left out, `main` takes both from `boundaries_from_environment(os.environ)` and runs the watch as the settings' instance.
- On a clone whose `origin/main` does not resolve, `run_watch` and `Watcher(...).evaluate` raise `GitError` whose text is `resolve origin/main failed (no exit status): origin/main does not resolve`.

Tests (the tester writes them): `tests/entry/test_watch_main.py` (new), on the `boundaries`, `human` and `clock` fixtures, with the story claim of `watch_support.push_story_claim` and `aged_claim` and the agents installed by the `installed_agents` fixture of `tests/conftest.py` (`pytestmark = pytest.mark.usefixtures("installed_agents")`). The environment criterion replaces `factory.entry.watch.boundaries_from_environment` with `monkeypatch.setattr` by a stand-in that returns the test's boundaries and `InstanceSettings` of the instance `factory-2`; the code under test, `main`, is not replaced. `tests/application/test_watcher_main_ref.py` (new), on a clone of an empty bare remote, as `tests/entry/test_watch.py::test_run_watch_without_origin_main_raises_git_error` builds it. No earlier test changes.

## Acceptance criteria

1. `main([], boundaries=b, instance="factory-1", out=out, err=err)`, with `FACTORY_INSTANCE` removed from the environment and the story `F0001-S0001` claimed by `factory-1` 1 minute before the clock under a 60-minute lease: it returns 0, the first line of `out` is `event: idle:-  F0001-S0001 is held by factory-1`, and `err` is empty.
2. `main` with given boundaries and instance, `out` and `err`, on a remote whose `factory/pipeline.yml` on `main` is not valid YAML: it returns 1, `out` is empty, and `err` is one line that starts with `factory-watch: `.
3. `main` with given boundaries and instance, and `out` and `err` left out (rows of one parametrized test, read with `capsys`): for the story of criterion 1, standard output starts with `event: idle:-  F0001-S0001 is held by factory-1` and standard error is empty; for the definition of criterion 2, standard output is empty and standard error is one line that starts with `factory-watch: `.
4. `main` with `boundaries_from_environment` replaced by the stand-in that gives the instance `factory-2`, and `F0001-S0001` claimed by `factory-2` 61 minutes before the clock under a 60-minute lease (rows of one parametrized test): with both left out (`main([], out=out, err=err)`), with only `instance="factory-1"` given, and with only `boundaries` given, it returns 0, `err` is empty, and the first line of `out` is `event: crash:F0001-S0001` (the settings' own claim past its lease; as another instance's claim it would be `expired:F0001-S0001`).
5. On a clone of an empty bare remote (rows of one parametrized test): `run_watch(...)` and `Watcher(boundaries, "factory-1").evaluate(definition)` each raise `GitError` whose `str` is exactly `resolve origin/main failed (no exit status): origin/main does not resolve`.
6. `make check` stays green.
7. docs: none. `docs/project-guide/watching.md`, *The watcher's command line*, and the operator guide's `factory-watch` section already say what `main` does with its streams, its instance and the environment, and that a missing `origin/main` ends with a git error.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python - "$d" <<'EOF'
import contextlib
import io
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.work_item_markdown import FrontmatterWorkItemWriter
from factory.domain.errors import GitError
from factory.domain.settings import InstanceSettings
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState
from factory.entry.watch import main
from factory.entry.wiring import build_boundaries

d = Path(sys.argv[1])
story = "factory/features/F0001-example/in-progress/F0001-S0001-first.md"
pipeline = 'contract: "1.0"\nproject_commands:\n  check: {time_limit: 10}\nroles:\n  coder: {write_paths: ["src/*"]}\nstages:\n  doing: {role: coder, next: [done], checks: [check]}\n  done: {}\n'


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=cwd, check=True, capture_output=True)


def write(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")


def watch(boundaries) -> None:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = main([], boundaries=boundaries, instance="self")
    print(status, repr(out.getvalue().splitlines()[:1]), repr(err.getvalue()))


def boundaries_of(name: str):
    git(d, "clone", "-q", str(d / "remote.git"), name)
    settings = InstanceSettings(repository_url="https://github.com/example/project.git", instance="self", checkout=d / name, state_directory=d / f"{name}-state", agent_home=d / "agents-home")
    return build_boundaries(settings, "unused", hosting=FakeHostingService())


git(d, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
empty = boundaries_of("empty")
try:
    main([], boundaries=empty, instance="self")
except GitError as error:
    print(error, flush=True)
git(d, "clone", "-q", str(d / "remote.git"), "human")
human = d / "human"
write(human, "factory/pipeline.yml", pipeline)
write(human, "factory/features/F0001-example/feature.md", "# Example feature\n")
write(human, story, "# First story\n")
git(human, "add", "-A")
git(human, "commit", "-q", "-m", "start")
git(human, "push", "-q", "origin", "main")
write(d / "agents-home", "agents/coder.md", "---\nmodel: sonnet\ntools: [Read, Write]\nbudget_usd: 1\n---\nDo the work.\n")
git(human, "switch", "-q", "-c", "work-item/F0001-S0001")
claim = Claim(instance="self", stage="doing", started_at=datetime.now(UTC) - timedelta(minutes=1), lease_duration=60)
write(human, story, FrontmatterWorkItemWriter().render(WorkItemDocument(state=WorkItemState(stage="doing", claim=claim), body="# First story\n")))
git(human, "commit", "-q", "-am", "doing starts")
git(human, "push", "-q", "origin", "work-item/F0001-S0001")
boundaries = boundaries_of("checkout")
watch(boundaries)
git(human, "switch", "-q", "main")
write(human, "factory/pipeline.yml", "contract: [\n")
git(human, "commit", "-q", "-am", "break the definition")
git(human, "push", "-q", "origin", "main")
boundaries.git.fetch()
watch(boundaries)
EOF
```
Expect: three lines, `resolve origin/main failed (no exit status): origin/main does not resolve`, `0 ['event: idle:-  F0001-S0001 is held by self'] ''` and `1 [] 'factory-watch: not valid YAML: did not find expected node content (line 2, column 1)\n'`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change, and the signatures of `main`, `run_watch` and `Watcher.evaluate` are concrete. Each of the four rules (given pair, streams with their `sys.stdout`/`sys.stderr` defaults, environment fallback, exact `GitError` text) has a criterion: 1 and 4, 1–3, 4, 5.
   Criteria: each can be tested by one function or one parametrized test. The failing sides are covered: an invalid definition (2 and 3) and the missing `origin/main` (5). Criterion 4 has a row for each omission (both left out, only `instance`, only `boundaries`). The own-claim `crash` against `expired` distinction is stated. 6 and 7 are the closing ones.
   Smoke test: runnable. Each `Expect:` value is a checkable string, namely the three printed lines. I did not run it.
   Architecture: tests only, in `tests/entry/` and `tests/application/`, mirroring the package. The stand-in replaces `boundaries_from_environment`, not the code under test. No earlier test changes.
   Scope: the story is not in `feature.md`'s Stories list because the feature acceptance proposed it. It sits inside the feature's goal, touches nothing in "Out of scope" (not `test_watcher_move_rule.py`, not the tick's judgement), and changes no code.
4. factory: started tests as self.
5. factory: crash 1: the run of stage tests ended without a result. Its work is discarded back to commit 89542f8b3d9d0cf21231592263b8f660ca9dd937.
6. factory: started tests as self.
7. tester: I wrote the tests for the five behaviour criteria. The story changes no code, so the new tests pass against today's `main`, `run_watch` and `Watcher`: one `make test` run ended `test: green` rather than red. This is expected here. The tests exist to kill the surviving mutants, so the coder has nothing to implement and only needs to confirm `make check`. `make lint` is green.

   - criterion 1: tests/entry/test_watch_main.py::test_main_watches_as_the_given_instance_on_the_given_boundaries
   - criterion 2: tests/entry/test_watch_main.py::test_main_writes_an_invalid_definition_to_the_given_error_stream
   - criterion 3: tests/entry/test_watch_main.py::test_main_writes_to_the_standard_streams_when_none_are_given (rows `held-story`, `invalid-definition`; read with `capsys`)
   - criterion 4: tests/entry/test_watch_main.py::test_main_takes_both_from_the_environment_when_either_is_left_out (rows `both-left-out`, `only-instance`, `only-boundaries`; the stand-in for `boundaries_from_environment` is set with `monkeypatch.setattr` and returns `local_settings` with instance `factory-2` and the test's boundaries)
   - criterion 5: tests/application/test_watcher_main_ref.py::test_an_unresolved_origin_main_raises_the_operators_git_error (rows `run_watch`, `watcher`; checks the exact `str` of the `GitError`)
   - criteria 6 and 7: nothing to test (`make check` green; docs: none)

   Files created: `tests/entry/test_watch_main.py` and `tests/application/test_watcher_main_ref.py`. No earlier test was changed.

   Every module imported. The test data is the invalid YAML `contract: [\n` pushed to `main`, and claims built with `watch_support.aged_claim`/`push_story_claim` at ages 1 and 61 minutes. I skipped the type check for this stage as instructed; the coder's `make check` covers it.

   `lint`: lint: green (0.0 s)
   `test`: test: green (48.6 s)
8. factory: started doing as self.
9. coder: I built nothing, because the story changes no code. The tester's new tests, `tests/entry/test_watch_main.py` and `tests/application/test_watcher_main_ref.py`, pass against `main`, `run_watch` and `Watcher` as they already are. I changed no file under `src/` or `tests/`. I ran `make check` once and it ended `check: green` (`test: green (46.6 s)`, total coverage 99.10 %).

   Main choice: I left the code alone and handed it forward. The alternative I rejected was touching `src/factory/entry/watch.py` to make it more testable, since the story's Interface says "No module under `src/factory/` changes". Refactor step: there is no diff of mine to read, so nothing needed changing. The journal changed nothing about what the task means, so `## Description` stays as it is.

   Noticed but not touched:
   - Lines 82-83 of `src/factory/entry/watch.py` are now covered, but line 87 still shows as uncovered. It is the `raise SystemExit(main())` under `if __name__ == "__main__":`, which only runs when the module itself is executed, so an in-process call to `main` can never reach it. The Description lists line 87 among the gaps, but no criterion asks for it. Covering it would take running the module in a subprocess, or a `# pragma: no cover`, which would be a code change. Both are for the reviewer or the human to weigh.
   - I did not run the mutation report (`make mutants`). The factory runs it after this stage and will show whether the 14 surviving mutants of `main` and the four `GitError` text survivors are now killed.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
10. factory: started review as self.
11. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: two new test files, `tests/entry/test_watch_main.py` and `tests/application/test_watcher_main_ref.py`. Nothing under `src/` changes.

    Groups 1 to 4 pass:
    - Group 1, acceptance criteria. Criteria 1 to 5 each have a test that checks what the criterion says, and the coder's entry 9 reports `check: green`.
      - Criterion 1 removes `FACTORY_INSTANCE`. A `main` that read the environment would therefore end with status 2, so the given pair is pinned.
      - Criterion 3 has two rows, one per stream. Each row catches a stream swapped or left as `None`.
      - Criterion 4 has three rows. The two rows that leave `boundaries` out pin "both from the environment". The `only-instance` row catches dropping `instance = settings.instance`, because the claim would then read `expired`.
      - Criterion 5 checks the exact `str` through both `run_watch` and `Watcher`.
      - The coder's entry has no `mutants` line, so I had no mutation report to read.
    - Group 2, architecture: tests only, in folders that mirror the package.
    - Group 3, security: nothing to flag.
    - Group 4, quality: the stand-in matches the shape of `boundaries_from_environment` (`src/factory/entry/wiring.py:205`). The `empty_clone` fixture builds its clone the way the story's Interface says to (`tests/entry/test_watch.py:220-222`). It copies no existing helper.

    Findings:
    1. The work item's `## Description` says lines 82-83 and 87 of `src/factory/entry/watch.py` were uncovered and that "This story pins all of that". Line 87, `raise SystemExit(main())` under `if __name__ == "__main__":`, is still uncovered, as the coder's entry 9 says, and no criterion asks for it. So the Description does not match what was built (item 5). Fix: the coder rewrites the Description to say that line 87 stays uncovered, because only running the module as a program reaches it. Alternatively, end with `question` if the human wants a criterion that runs the module in a subprocess.

    Earlier tests: none. `git diff --name-status main...HEAD` shows only added test files, so no earlier test file changed.
12. factory: started doing as self.
