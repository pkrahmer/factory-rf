---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 536
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-04T03:26:57.994769Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T03:26:35.170738Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T03:26:35.177376Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T03:26:52.156374Z'
  stage: intake
  run: 59fcf7c039984a5bbea50f25ce23bf37
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T03:26:57.994769Z'
  stage: tests
---

# The Debian packages decision points to the entry that superseded it

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

`docs/decisions.md` has the entry *Debian's packages follow the base image's release* (2026-11-01, F0047-S0006). It still says that the stage image installs seven Debian packages, `nodejs` and `npm` among them, and that `tests/test_stage_image.py` allows exactly those seven names. Since F0049-S0001, `vm/Dockerfile` installs six: `xz-utils` replaces `nodejs` and `npm`. `STAGE_PACKAGES` in `tests/test_stage_image.py` lists those six. The later entry *The factory's tools live apart, under `/opt/factory`, with their own Node* says that it supersedes the old one for those two packages. The old entry does not point forward, although the log's convention is that it should: other superseded entries carry a line `- Superseded in part by "<entry>": <what changed>.` (*Every tool of the machine's image is pinned*, for example, carries one that points to this very entry). A newcomer who reads the log from the top meets the seven packages first, with nothing that sends them on. This story adds that one line to the old entry. It does not rewrite the entry's other lines, which stay as the record of what was decided on 2026-11-01. No code and no test change.

## Interface

- No module under `src/factory/` changes, and no test. The story changes `docs/decisions.md` only.
- The line the documenter adds as the last bullet of *Debian's packages follow the base image's release*, in the form the log already uses: `- Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node": the image installs six Debian packages, `xz-utils` in place of `nodejs` and `npm`, and `tests/test_stage_image.py` allows those six names.`

## Acceptance criteria

1. `docs/decisions.md`, the entry *Debian's packages follow the base image's release*: it ends with one bullet that starts `Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node"` and names the six packages and `xz-utils` in place of `nodejs` and `npm`. The entry's other bullets are unchanged, and no other entry of the log changes. Without the line, the entry has no forward pointer at all, which is the state this story ends.
2. `make check` stays green.
3. docs: `docs/decisions.md` as criterion 1 says. `README.md`, `docs/operator-guide.md` and the project guide: none, because they already name the six packages (`docs/operator-guide.md`, *The stage image*) or do not name them at all.

## Smoke test

```bash
grep -c 'Superseded in part by "The factory.s tools live apart' docs/decisions.md
sed -n '/^## Debian.s packages follow the base image.s release/,/^## /p' docs/decisions.md | grep -c 'xz-utils'
uv run python -m factory.entry.check_documents
```

Expect: `1`, then `1`, then `documents ok` (uv may print a `Bytecode compiled` line before it).

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names one file (`docs/decisions.md`), one entry (*Debian's packages follow the base image's release*, found at line 1306) and the exact bullet text to add as its last bullet, in the log's existing `Superseded in part by "<entry>": ...` form. The target entry *The factory's tools live apart, under `/opt/factory`, with their own Node* exists (line 1450). No module or signature is involved, and the story says so.
   - Criteria: criterion 1 is checkable by one test or grep: the bullet is last in the entry, starts with the given text and names the six packages and `xz-utils` in place of `nodejs` and `npm`. It also says the other bullets and other entries are unchanged. There are no rules with a failing side: the story is a one-line docs change. The Interface states no behaviour beyond the line itself. Criteria 2 and 3 are the closing ones, in order.
   - Smoke test: the three commands are runnable. Two greps and the document check, no pytest, so no `-q` problem. Each `Expect:` (`1`, `1`, `documents ok`) can be checked against the output. The `.` in the grep patterns stands for the apostrophe.
   - Architecture: the change is documentation only, in the decision log, which the documenter stage keeps. It touches no layer. `STAGE_PACKAGES` in `tests/test_stage_image.py` does list the six names the line states.
   - Scope: it is within F0049 (the image split that replaced `nodejs` and `npm` with `xz-utils` in S0001). It is not in the feature's "Out of scope", and it changes no test of another story.
4. factory: started tests as vm.
