# What a stall shows on the pull request: the red check's output as a block, and the stage label

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0005 ran the stage protocol end to end and found two things a stall leaves wrong on the pull request. The fix needs no new decision rule.

First, the note of a red check. `StageFinisher` passes the stall detail `` `<command>`\n<the last 15 lines> ``, and `stall_note` puts it inline: the follow-up sentence is glued to make's error line (`make: *** [Makefile:6: check] Error 1. Retrying on the next tick.`), and the output is rendered as Markdown. GitHub then drops `<module>` from a traceback, turns `__init__` into bold, and so on. This story puts a multi-line detail's first line in the note's sentence, keeps the follow-up on that first line, and puts the remaining lines in a fenced `text` block below.

Second, the label. A stall writes no label. Only the result commit (`StageFinisher`, step 8) does. So a work item whose first stage stalls has a draft pull request without its `stage:` label until its first result commit. After this story `StallService.stall` writes `labels_for(<the stalled state>)` once the note is posted, like the result commit: written, never read back.

Kept as it is, for the human to revisit while refining: the journal's stall entry keeps the tail as continuation lines (`stall_cause` is unchanged). The alternative to labelling in the stall is to label when `WorkItemOpening.ensure_pull_request` creates the draft; I chose the stall because it also covers a pull request the stall itself had to create. This keeps FEATURE decision 11 (the note names the attempt and the cause) and the scope's "labels written as a projection of the stage".

## Interface

`src/factory/domain/post_texts.py` (changed)

```python
def stall_note(
    reason: StallReason, attempts: int, attempts_cap: int, *, detail: str = ""
) -> str: ...
```

- Trailing line breaks of `detail` are removed first.
- A `detail` without a line break (or empty) gives the note as before: `Stalled (attempt <n> of <cap>): <stall_cause(reason, detail)>. <follow-up>`, where `<follow-up>` is `Retrying on the next tick.` below the cap and `The attempts cap is reached; the factory asks you next.` at or above it.
- A `detail` with a line break gives these lines joined by `\n`, with no trailing newline:
  1. `Stalled (attempt <n> of <cap>): <stall_cause(reason, <the detail's first line>)>. <follow-up>`;
  2. an empty line;
  3. the opening fence `<fence>text`;
  4. every remaining line of the detail, unchanged (leading spaces and Markdown characters kept);
  5. the closing fence `<fence>`.
- `<fence>` is three backticks. It is one backtick longer than the longest run of consecutive backticks in the remaining lines when that run is three or longer.
- `stall_cause` is unchanged.

`src/factory/application/stalls.py`, `StallService.stall` (one step added)

- Step 7, after step 6 (the note) returned, whether `"posted"` or `"already_posted"`: `HostingService.set_labels(pull_request, labels_for(<the stalled state>))`, with `labels_for` from `factory.domain.labels`.
- A `HostingServiceError` from `set_labels` propagates. The stall commit stays pushed and the note stays posted. When step 6 raised, no label is written.
- No other step changes, and `StallResult` is unchanged.

Tests: the new files `tests/domain/test_stall_note_block.py` (criteria 1 to 6) and `tests/application/test_stall_labels.py` (criteria 7 to 12). Stages run through `StageRunner` with `FakeAgentRuntime` and `FakeHostingService`, and the checks are real `make` targets pushed with `human.push_file`, as in `tests/application/test_stage_run.py`. No existing test changes. `tests/domain/test_stall_texts.py`, `tests/application/test_stalls.py` and `tests/application/test_after_agent.py` use one-line details only. `tests/application/test_stage_finish.py::test_the_stall_note_of_a_red_check_carries_the_tail_of_its_output` posts a multi-line detail but checks only that `line 7` to `line 20` and `Error 1` are in the note and `line 6` is not, so it passes unchanged. No existing test reads the labels after a stall.

## Acceptance criteria

1. `stall_note("check_red", 1, 2, detail="`check`\nline a\nline b")` returns exactly `` Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick. ``, an empty line, `` ```text ``, `line a`, `line b`, `` ``` ``, joined by `\n` with no trailing newline.
2. At the cap, `stall_note("check_red", 2, 2, detail="`check`\nline a")` has the first line `` Stalled (attempt 2 of 2): a check is red after the stage: `check`. The attempts cap is reached; the factory asks you next. `` and ends with the closing fence. The note contains no `retry` in any case.
3. A one-line detail gives the note as before: `stall_note("check_red", 1, 2, detail="3 failed")` is `Stalled (attempt 1 of 2): a check is red after the stage: 3 failed. Retrying on the next tick.`, and `stall_note("died", 1, 2)` is `Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick.`.
4. Trailing line breaks do not make a block and do not reach one: `detail="3 failed\n\n"` gives the note of criterion 3, and `stall_note("check_red", 1, 2, detail="`check`\nline a\n\n")` equals `stall_note("check_red", 1, 2, detail="`check`\nline a")`, whose last two lines are `line a` and the closing fence.
5. The remaining lines are kept as they are. For the detail `` `check` ``, `  File "x.py", line 1, in <module>`, `make: *** [Makefile:6: check] Error 1`, both lines appear in the block unchanged, leading spaces included.
6. The fence outgrows the tail. A remaining line `` ``` `` gives the fences ` ````text ` and ` ```` ` (four backticks). A run of five backticks gives six. A remaining line with a run of two backticks (``` ``x`` ```) keeps three.
7. Through `StageRunner`, a red `check` prints `line 1` to `line 20` and then make's error line. The posted note's first line ends with `Retrying on the next tick.`, and its block holds `line 7` to `line 20` and make's error line in that order (the last 15 lines), and not `line 6`. The journal's stall entry still holds `line 20` and make's error line.
8. A new work item whose first stage (`intake`) stalls with `died` has the labels `["stage:intake"]` on its pull request after `StageRunner.run`.
9. A merge-conflict stall at `doing` leaves the labels `["stage:doing"]`.
10. When the note is `"already_posted"` (the same stall key posted before), the labels are still written.
11. A `set_labels` that fails (`hosting.fail_next("set_labels")`) makes `stall` raise `HostingServiceError`. The remote branch then holds the stall commit with `attempts` raised by one, and the note is posted once.
12. A `post_comment` that fails makes `stall` raise `HostingServiceError`, and the pull request of a first-stage stall has the labels `[]`.
13. make check stays green.
14. docs: `docs/operator-guide.md`, "A stall by a red check", shows the note of a red check with its output in a code block below the sentence. "A stall: the stall note" says that a stall writes the `stage:` label too. `docs/project-guide.md`, "Stalls", gives `stall_note`'s block rule (first line in the sentence, the rest fenced, the fence longer than any backtick run) and step 7. `docs/decisions.md` records why the output is fenced (GitHub renders a comment as Markdown) and why the stall writes the label.

## Demo

```bash
uv run python -c "
from factory.domain.post_texts import stall_note
print(stall_note('check_red', 1, 2, detail='\`check\`\n  File \"x.py\", line 1, in <module>\nmake: *** [Makefile:6: check] Error 1'))
print('--')
print(stall_note('check_red', 1, 2, detail='3 failed'))
"
```
Expect: the first line is `` Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick. ``. Next come an empty line, `` ```text ``, `  File "x.py", line 1, in <module>` with its two leading spaces, `make: *** [Makefile:6: check] Error 1` and `` ``` ``. Then the line `--`, and last `Stalled (attempt 1 of 2): a check is red after the stage: 3 failed. Retrying on the next tick.`.

```bash
uv run pytest tests/application/test_stall_labels.py
```
Expect: the last line says `passed`, and the output holds no `failed` and no `error`.

## Log (append only)

1. 2026-10-14 human: created.
