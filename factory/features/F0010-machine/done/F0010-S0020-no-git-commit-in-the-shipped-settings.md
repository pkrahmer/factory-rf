---
stage: done
pr: 138
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# No git commit in the shipped settings

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The shipped agents and their shared settings contradict each other on one point. F0010-S0017 carried v1's pipeline rules into every shipped agent and rewrote v1's R10 for v1.1: "You do not commit either: leave your changes in the working tree for the factory's commit" (`claude/agents/*.md`, `## Rules`). The factory makes the result commit itself. But `claude/settings.json`, shipped by F0010-S0012 with v1's permissions, still allows `Bash(git add *)` and `Bash(git commit *)`, and `docs/project-guide.md` describes them as "the read and commit git commands".

The documenters of S0017 (entries 10 and 12) and S0012 noted this and did not touch it, because it lies outside their lane. An allowed command that the instructions forbid is a key with no effect, or one with the wrong effect: FEATURE.md promised settings where "each key [has] an effect". In a real image the agent user has no git identity, so its `git commit` fails or makes a commit under an identity nobody chose. The commit then sits between the claim and the factory's result commit.

This story takes `git add` and `git commit` out of the allow list and puts them on the deny list. The model then gets a refusal from the runtime, not a commit.

This changes `tests/test_claude_files.py::SETTINGS`, which F0010-S0012's tester wrote. Under `CLAUDE.md` that needs the human's permission. The human gives it by promoting this story: the tester changes exactly the two lists in `SETTINGS`, and nothing else in that file.

## Interface

`claude/settings.json`:

- `permissions.allow` drops `Bash(git add *)` and `Bash(git commit *)` and keeps every other entry, in the same order.
- `permissions.deny` gains `Bash(git add*)` and `Bash(git commit*)` after `Bash(git branch -D*)`.
- `env` stays `{"CLAUDE_CODE_FORK_SUBAGENT": "0"}`.

No code changes. `tests/test_claude_files.py::SETTINGS` is changed to match, as the Assignment allows.

## Acceptance criteria

1. `claude/settings.json` parses as JSON. Its `permissions.allow` holds no entry that starts with `Bash(git add` or `Bash(git commit`, and still holds `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git show*)` and `Bash(git rev-parse*)`.
2. Its `permissions.deny` holds `Bash(git add*)` and `Bash(git commit*)`, and still holds `Bash(git push*)` and `Bash(gh *)`.
3. The settings equal `tests/test_claude_files.py::SETTINGS` after the tester's change (`settings == SETTINGS`, so each list keeps its order).
4. The `## Rules` of every shipped agent still holds the sentence ``You do not commit either``.
5. `make check` stays green.
6. docs: `docs/project-guide.md`, "The settings", lists the git commands an agent may run (`status`, `diff`, `log`, `show`, `rev-parse`) and names `add` and `commit` among the denied ones, with the reason: the factory makes the result commit (R10). `docs/operator-guide.md`, "The shipped agents and settings", names `git add` and `git commit` among the denied commands, with the same reason.

## Demo

```bash
uv run python -c "import json; s = json.load(open('claude/settings.json')); print([a for a in s['permissions']['allow'] if a.startswith('Bash(git')]); print([d for d in s['permissions']['deny'] if 'add' in d or 'commit' in d])"
```
Expect: `['Bash(git status*)', 'Bash(git diff*)', 'Bash(git log*)', 'Bash(git show*)', 'Bash(git rev-parse*)']`, then `['Bash(git add*)', 'Bash(git commit*)']`.

```bash
grep -c 'You do not commit either' claude/agents/*.md
```
Expect: seven lines, each ending in `:1`.

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: concrete. `claude/settings.json` allow/deny edits are exact and checked against the file as it stands today (allow holds `git add *` and `git commit *`; deny ends its git block with `Bash(git branch -D*)`, so the insertion point exists). `env` is unchanged. No code, so no signatures are needed.
   - Criteria: 1 and 2 are testable by one function each (membership and absence). 3 is `settings == SETTINGS`, so order is covered. 4 is a single check that all seven agents hold the sentence, and I confirmed that they do today. Every rule has its failing side: criterion 1 says the entries are gone from allow and criterion 2 says they are denied. 5 and 6 are the usual closing criteria.
   - Demo: both commands are runnable. The first prints two lists, and the Expect line gives them exactly. The second prints seven lines ending in `:1`, which matches the seven files in `claude/agents/`.
   - Architecture: this is a shipped data file plus a test constant. It touches no layer, and it matches the agents' rule "You do not commit either" (R10).
   - Scope: it fits FEATURE.md ("each key has an effect", settings and shipped agents) and nothing in "Out of scope" covers it. The change to `tests/test_claude_files.py::SETTINGS` is covered by decision 37 (6) and the Assignment, which limit it to the two lists and nothing else in that file.
3. tester: I wrote the tests from the acceptance criteria. Four tests now fail, and each fails because `claude/settings.json` has not been changed yet. No module is missing, so there were no import errors. `make lint` is green.

   Criterion → test:
   - criterion 1: `tests/test_claude_settings_git.py::test_allow_list_holds_no_git_add_or_commit` checks that no allow entry starts with `Bash(git add` or `Bash(git commit`. `tests/test_claude_settings_git.py::test_allow_list_keeps_the_read_git_commands` is parametrized over status, diff, log, show and rev-parse.
   - criterion 2: `tests/test_claude_settings_git.py::test_deny_list_holds_git_add_and_commit_beside_push_and_gh` is parametrized over `Bash(git add*)`, `Bash(git commit*)`, `Bash(git push*)` and `Bash(gh *)`.
   - criterion 3: `tests/test_claude_files.py::test_settings_are_the_shared_permissions_and_environment` is unchanged. Its expected value, `SETTINGS`, is the one changed in `tests/test_claude_files.py`, below.
   - criterion 4: `tests/test_claude_settings_git.py::test_rules_section_still_forbids_the_agent_to_commit` is parametrized over the seven shipped agents and looks for `You do not commit either` in the `## Rules` section.
   - criteria 5 and 6: these are the closing criteria (`make check`, docs), so they have no test.

   Files:
   - I created `tests/test_claude_settings_git.py`.
   - I changed `tests/test_claude_files.py`, as the Assignment allows. I changed only the two lists in `SETTINGS`:
     - allow: `Bash(git add *)` and `Bash(git commit *)` are removed, and every other entry keeps its order.
     - deny: `Bash(git add*)` and `Bash(git commit*)` are inserted after `Bash(git branch -D*)`.
     - Nothing else in that file changed.

   Rejected: I did not add the tests for criteria 1, 2 and 4 to `tests/test_claude_files.py` or `tests/test_claude_agent_texts.py`. Another story wrote those files, and the Assignment allows a change to `SETTINGS` only.

   Currently failing, all because `claude/settings.json` still has the old lists:
   - `test_settings_are_the_shared_permissions_and_environment`
   - `test_allow_list_holds_no_git_add_or_commit`
   - `test_deny_list_holds_git_add_and_commit_beside_push_and_gh[Bash(git add*)]`
   - `test_deny_list_holds_git_add_and_commit_beside_push_and_gh[Bash(git commit*)]`

   The criterion 4 tests and the kept-entry rows pass already.

   Next: the coder edits `claude/settings.json` only.

   `make lint`: lint: green
   `make test`: FAILED tests/test_claude_settings_git.py::test_deny_list_holds_git_add_and_commit_beside_push_and_gh[Bash(git commit*)]
4. coder: I edited `claude/settings.json` and nothing else (commit 17fede5).
   - `permissions.allow`: I removed `Bash(git add *)` and `Bash(git commit *)`. The other entries keep their order, and `Bash(git rev-parse*)` now closes the git block.
   - `permissions.deny`: I inserted `Bash(git add*)` and `Bash(git commit*)` after `Bash(git branch -D*)` and before `Bash(gh *)`.
   - `env` is unchanged.
   - The file now equals `tests/test_claude_files.py::SETTINGS`. All four tests that were failing now pass, and `make check` is green (coverage 99.54 %).

   Design: the deny patterns have no space before `*` (`git add*`), as the Interface says and as the other deny entries are written. The pattern therefore also covers forms like `git add-…` or a bare `git commit`. Rejected: removing the two entries from allow without adding them to deny. The runtime would then ask for permission instead of refusing, and an unattended run cannot answer.

   Refactor: nothing to change. The diff is two list edits in a data file.

   Noticed, not touched: `docs/project-guide.md` still calls the allowed git commands "the read and commit git commands". `docs/operator-guide.md` still has to name `git add` and `git commit` among the denied commands. Both belong to the documenter (criterion 6).

   `make check`: check: green
5. reviewer: no findings.
      - Criteria: each criterion has a test, and I read each test against its criterion. Criterion 1 is covered by `tests/test_claude_settings_git.py::test_allow_list_holds_no_git_add_or_commit`, which checks that the entries are absent, the failing side. `test_allow_list_keeps_the_read_git_commands` covers the five kept entries, one row each. Criterion 2 is covered by `test_deny_list_holds_git_add_and_commit_beside_push_and_gh`, with four rows. Criterion 3 is covered by `tests/test_claude_files.py::test_settings_are_the_shared_permissions_and_environment` against `SETTINGS`. The diff to `SETTINGS` changes only the two lists, as the Assignment allows. Criterion 4 is covered by `test_rules_section_still_forbids_the_agent_to_commit`, with one row per agent in `SHIPPED_NAMES`. The coder's entry records `make check` as green.
      - Interface: `claude/settings.json` matches it exactly. Allow drops `Bash(git add *)` and `Bash(git commit *)`, and the other entries keep their order. Deny inserts `Bash(git add*)` and `Bash(git commit*)` after `Bash(git branch -D*)`. `env` is unchanged.
      - Architecture and security: no code under `src/` changes. The diff adds no suppression markers. The tests reuse the existing helpers `shipped_agents.AGENT_HOME`, `SHIPPED_NAMES` and `front_matter_and_body`, and `factory.domain.sections.section_text`.
      - Quality: the tests follow the conventions in `CLAUDE.md` (parametrized rows, module docstring, no mocks). `_permissions` is a small private reader. It does not duplicate an existing helper; `test_claude_files.py` reads the settings inline.
      - Hygiene: the coder's entry names its main decision, to deny the two commands rather than only drop them from allow, and the reason. The docs criterion (6) still says what the documenter has to change. The coder noted that `docs/project-guide.md` still says "the read and commit git commands"; the documenter fixes that under criterion 6.
6. documenter: I changed two files, and `make check` is green after the edits.
   - `docs/project-guide.md`, "The settings": the allowed git commands are now `status`, `diff`, `log`, `show` and `rev-parse`. The old text called them "the read and commit git commands". The denied list now starts with `git add` and `git commit`, with the reason: the factory makes the result commit (R10), the agents' Rules say "You do not commit either", and the runtime refuses a denied command instead of asking for a permission nobody can give.
   - `docs/operator-guide.md`, "The shipped agents and settings": `git add` and `git commit` are named among the denied commands. The reason is the same, and I added that an agent user has no git identity of its own.
   - Cross-read against the diff and found current: `claude/settings.json`, which matches both docs, and `README.md`, which does not mention the git permissions.
   - Findings: none. The code matches the Interface.
   - Stale text I saw and did not touch: nothing unrelated to this story.

   `make check`: check: green
7. demo: both commands met their Expect lines, and the demo contradicts no criterion. No findings.

   1. Read the git entries in the allow list and the add/commit entries in the deny list of `claude/settings.json`:
   ```
   ['Bash(git status*)', 'Bash(git diff*)', 'Bash(git log*)', 'Bash(git show*)', 'Bash(git rev-parse*)']
   ['Bash(git add*)', 'Bash(git commit*)']
   ```
   Met: both lists match the Expect line exactly, in the same order.

   2. `grep -c 'You do not commit either' claude/agents/*.md`:
   ```
   claude/agents/acceptance-reviewer.md:1
   claude/agents/coder.md:1
   claude/agents/documenter.md:1
   claude/agents/intake.md:1
   claude/agents/reviewer.md:1
   claude/agents/smoke-tester.md:1
   claude/agents/tester.md:1
   ```
   Met: seven lines, each ending in `:1`. There are seven files in `claude/agents/`.

   Criteria cross-check:
   - Criterion 1: there is no `git add` or `git commit` entry in the allow list, and the five read commands are still there.
   - Criterion 2: the full deny list is `git push*, git checkout*, git switch*, git merge*, git pull*, git rebase*, git reset*, git branch -D*, git add*, git commit*, gh *, rm -rf *`. It holds add and commit right after `git branch -D*`, and still holds push and `gh *`, as the Interface says.
   - Interface: `env` is still `{"CLAUDE_CODE_FORK_SUBAGENT": "0"}`.
   - Criterion 4: command 2 confirms it.
   - Criteria 3, 5 and 6: I did not re-run these. The tests, `make check` and the docs are covered by the earlier entries (3–6) and the factory's checks.
8. done (pull request merged); cost: 6 runs, 32.0 min, 31 turns, 81k tokens in (431k more from cache), 9k out, $0.88
