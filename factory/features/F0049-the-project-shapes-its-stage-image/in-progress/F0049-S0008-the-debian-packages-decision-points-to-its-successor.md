---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 536
comments_read: [6621759488]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-04T03:33:57.510832Z'
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
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-04T03:27:28.264971Z'
  stage: tests
  run: 3f9c8319bb4a41cbb8524b8cdedd5ce5
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-04T03:31:23.857353Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T03:31:27.196446Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T03:31:43.358595Z'
  stage: tests
  run: 7f4d6a0a96a04d7fb98bce41ba167587
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T03:31:49.451049Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-04T03:33:51.511979Z'
  stage: doing
  run: e580696a5f4d480cab573617775e584f
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-04T03:33:57.510832Z'
  stage: review
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
5. tester: I wrote no test and changed no file. I'm stopping at step 1, because the work item and the tester's role disagree.

   The conflict: the Description says "No code and no test change". The Interface says "No module under `src/factory/` changes, and no test. The story changes `docs/decisions.md` only." But criterion 1 can be tested: the last bullet of *Debian's packages follow the base image's release* must start with the given text and name the six packages and `xz-utils` in place of `nodejs` and `npm`, and the other bullets and entries must stay unchanged. My role is to write one test per criterion. Other stories have pinned decision-log text in tests before, for example `tests/test_claude_agent_texts_decision_log.py`.

   Options:
   (a) No test for this story. Criterion 1 is checked by the smoke test (the two greps plus `check_documents`) and by the reviewer. Criteria 2 and 3 are the closing ones and get no test either way. I would end `doing` with no test files, and the coder and documenter go straight to the docs change.
   (b) Read "no test change" as "no existing test changes". I would add one new test module, `tests/test_decision_log_debian_packages.py`. Its test, `test_debian_packages_entry_points_to_its_successor`, would read `docs/decisions.md` and check that the entry's last bullet starts with `Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node"` and names `xz-utils`, `nodejs` and `npm`. The test fails until the documenter adds the line. It cannot check "the other bullets and entries are unchanged" without copying the old text into the test, so the reviewer would still check that part against the diff.

   I would choose (a), because the Description and Interface both rule out a test, and the human wrote them. I'll proceed as you say.
6. 2026-11-04 human: (a): no test for this story; the smoke test and the reviewer check criterion 1.
7. factory: started tests as vm.
8. tester: I wrote no tests and changed no file, as the human answered in entry 6 (option (a)): this story gets no test, and the smoke test and the reviewer check criterion 1.

   - criterion 1: no test. The smoke test (two greps and `check_documents`) and the reviewer check it against the diff of `docs/decisions.md`.
   - criterion 2: no test. It is the closing `make check` criterion.
   - criterion 3: no test. It is the closing `docs:` criterion.

   Files created: none. Modules the test run could not import: none, because there is no new test, so I skipped the step-2 test run. `make lint` passes with the working tree unchanged. Nothing is red on the branch: the coder has no test to satisfy, and the work is the one bullet that the Interface names, which the documenter adds to `docs/decisions.md`.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I built nothing and changed no file. This story changes only `docs/decisions.md`. Under `CLAUDE.md` (*Docs*), the documenter keeps the decision log and the coder does not write it. The tester wrote no test (entries 6 and 8), so there was no failing test to make pass. I ran `make check` on the unchanged tree and it ended `check: green`. The working tree is clean.

    - Main choice: I left the bullet the Interface names for the docs stage to add as the last bullet of *Debian's packages follow the base image's release*. The alternative was to add it myself in this stage, since it is a single line. I rejected that because the decision log belongs to the documenter, and a coder edit there would cross that line.
    - Refactor: there is no diff, so there was nothing to refactor.
    - Description: the journal did not change what the task means. The human's answer (entry 6) settles only that this story gets no test, and the Description already says "No code and no test change".
    - Noticed, not touched: nothing.

    `check`: check: green (not run again: passed on tree c75cce644896 at 2026-11-04T02:57:19Z)
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
11. factory: started review as vm.
