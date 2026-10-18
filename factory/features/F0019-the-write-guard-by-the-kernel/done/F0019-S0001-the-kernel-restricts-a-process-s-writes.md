---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 220
comments_read: [6251100326]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T14:29:30.289261Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T14:29:30.296920Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T14:29:47.102570Z'
  stage: intake
  run: 1255cbef6d9b490183b8668bc55ae5c0
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T14:30:30.950183Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T14:30:48.929141Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T14:31:06.574450Z'
  stage: intake
  run: 64d0427494bf44c4bd869b6fc77849e8
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T14:31:26.615271Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T14:34:27.381014Z'
  stage: tests
  run: 60db87c4e3874528a2a4a109e9db68b5
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T14:34:47.333817Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-18T14:37:34.939289Z'
  stage: doing
  run: ee04707d4eac4468b2d554045cb67307
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-18T14:37:55.065164Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-18T14:38:54.221370Z'
  stage: review
  run: 589bbc15d5414ce795d6e92f229326ef
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-18T14:39:14.245727Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-10-18T14:40:39.661134Z'
  stage: docs
  run: d340de66ef3d40e8b70d85b3dba6c02f
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-18T14:40:59.655074Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-10-18T14:41:21.376877Z'
  stage: smoke-test
  run: bed651d0e724473c99ef140104652bf9
- number: 17
  speaker: factory
  kind: done
  at: '2026-10-18T14:42:38.961470Z'
  stage: approval
---

# The kernel restricts a process's writes (Landlock)

## Description

The write guard by the kernel starts with one adapter: a process asks the kernel, through Landlock, to refuse every write of its own and of every process it starts, except beneath the folders and on the single files it names. This story builds that adapter on the standard library's `ctypes` (no new dependency, feature decision 1), the domain's minimum ABI with its fault text, and the error a rule that cannot be made raises. Nothing calls the adapter yet: the wrapper `factory-confine` (S0002) is its first user, the runtime (S0004) the wrapper's. The hook `factory-guard` and the undo stay as they are. The rules handle the twelve write rights of ABI 3 and nothing else, so reading, executing and the network stay open (feature decision 2); a folder rule allows all twelve beneath the folder, a file rule only writing and truncating that file in place (feature decision 3). Every path is checked before the first system call, so a refused rule leaves the process unrestricted (feature decision 4).

## Interface

`factory.domain.confinement` (`domain`, new module):

```python
LANDLOCK_MINIMUM_ABI = 3

def abi_fault(abi: int) -> str | None:
    """The fault of a kernel that offers Landlock ABI `abi`, or `None` when it suffices."""
```

- `abi_fault(n)` is `None` for `n >= 3`, and for `n < 3` exactly `f"the kernel offers Landlock ABI {n}, the write guard needs ABI 3 or higher"` (the number written as `LANDLOCK_MINIMUM_ABI`).

`factory.domain.errors` (`domain`):

```python
class ConfinementError(FactoryError):
    """A write restriction that cannot be made; the message names the path or the call."""

    detail: str

    def __init__(self, detail: str) -> None: ...
```

- The message is `detail` itself, without a prefix.

`factory.adapters.landlock` (`adapters`, new module):

```python
WRITE_RIGHTS = 0x7FF2  # the twelve write rights of ABI 3: bits 1 and 4 to 14
FILE_RIGHTS = 0x4002   # write a file and truncate it: bits 1 and 14

def abi_version() -> int:
    """The Landlock ABI the kernel offers; 0 when it offers none."""

def restrict_writes(folders: Sequence[Path], files: Sequence[Path]) -> None:
    """Refuse every write of this process and its children but beneath `folders` and on `files`."""
```

- `abi_version` calls `landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` (system call 444, flag 1) and returns its result; a negative result (no Landlock, or a seccomp profile that refuses the call) is `0`. It restricts nothing.
- `restrict_writes` first checks every path, folders before files, each in the given order, with `os.lstat`, and raises `ConfinementError` at the first that fails, before any system call: a path that does not exist is `f"cannot open {path}: {strerror}"` (`No such file or directory`); a symbolic link is `f"{path} is a symbolic link"`; a path of `folders` that is no folder is `f"{path} is not a folder"`; a path of `files` that is a folder is `f"{path} is a folder"`.
- It then creates a ruleset whose attribute holds only `handled_access_fs = WRITE_RIGHTS` (8 bytes), adds one rule per path with `landlock_add_rule` (445, `LANDLOCK_RULE_PATH_BENEATH` = 1, a packed `{u64 allowed_access; s32 parent_fd}` with a descriptor opened `O_PATH | O_CLOEXEC`, closed after the call): `WRITE_RIGHTS` for a folder, `FILE_RIGHTS` for a file; sets `prctl(PR_SET_NO_NEW_PRIVS = 38, 1, 0, 0, 0)` and calls `landlock_restrict_self` (446). A failing call raises `ConfinementError` `f"{call} failed: {strerror}"`, the call named `landlock_create_ruleset`, `landlock_add_rule for {path}`, `prctl PR_SET_NO_NEW_PRIVS` or `landlock_restrict_self`. The ruleset's descriptor is closed in every case.
- Empty `folders` and `files` are allowed: every write is then refused.
- A second call in a restricted process stacks: a write must be allowed by both rulesets.
- Under the restriction a refused write fails with `EACCES` (`PermissionError: [Errno 13] Permission denied`); reads are not restricted.

Tests (the tester writes them): `tests/domain/test_confinement_abi.py`, `tests/adapters/test_landlock.py`. Every call of `restrict_writes`, also one expected to raise, runs in a child process the test starts (`sys.executable -c <code>`, its paths under `tmp_path`), never in the pytest worker; `abi_version` may run in-process. No test is skipped without Landlock (feature decision 18). Not tested, because no test can make the kernel refuse them: a failing system call (`landlock_create_ruleset`, `landlock_add_rule`, `prctl`, `landlock_restrict_self`), `abi_version`'s negative result, and the closing of the descriptors after such a failure.

## Acceptance criteria

1. `abi_fault` returns `"the kernel offers Landlock ABI 0, the write guard needs ABI 3 or higher"` for 0, `"the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher"` for 2, and `None` for 3 and for 7 (four rows of one parametrized test).
2. `abi_version()` returns an `int` of at least 3 on the machine the tests run on (v1.1's container, ABI 7), and a child process that calls it can afterwards still write a new file in `tmp_path`.
3. In a child process that calls `restrict_writes([A], [F])`, with A a folder and F an existing file in another folder P, and O a third folder, all under `tmp_path`, each attempt has its result (rows of one parametrized test, one child per row): a new file in A is written; a new folder in A is made; a new file in a folder made in A is written; an existing file in A is deleted; a symbolic link made in A is created; a file in A renamed to another folder in A succeeds; F is appended to; F is opened for writing and truncated; a new file in O raises `PermissionError` with errno 13; a new file in `tmp_path` itself raises it; F renamed to P/moved raises it; F deleted raises it; a symbolic link made in O raises it; an existing file in O is read and its text returned; a shell started by the child (`sh -c 'echo x > O/c'`) exits non-zero and `O/c` does not exist afterwards.
4. In a child process, `restrict_writes` raises `ConfinementError` with the exact message for each refused input, and afterwards the same child still writes a new file in O (nothing was restricted): a missing folder in `folders` (`cannot open <path>: No such file or directory`); a missing file in `files` (the same text); a file in `folders` (`<path> is not a folder`); a folder in `files` (`<path> is a folder`); a symbolic link to a folder in `folders` and one to a file in `files` (`<path> is a symbolic link`) (rows of one parametrized test).
5. In a child process, `restrict_writes([], [])` makes a new file in A raise `PermissionError` with errno 13, while an existing file in A is still read.
6. In a child process that calls `restrict_writes([A, B], [])` and then `restrict_writes([A], [])`, a new file in A is written and a new file in B raises `PermissionError` with errno 13 (rows of one parametrized test).
7. In a child process, `/proc/self/fd` holds as many entries after `restrict_writes([A], [F])` as before it: the ruleset's descriptor and each rule's descriptor are closed.
8. `ConfinementError("x").detail` is `"x"` and `str(ConfinementError("x"))` is `"x"`.
9. In a child process, `restrict_writes` raises `ConfinementError` with the message of the first failing path (rows of one parametrized test): a missing folder in `folders` and a missing file in `files` give the folder's message; two missing folders give the first one's message; two missing files give the first one's message.
10. `make check` stays green.
11. docs: `docs/project-guide.md` gets a section *The kernel's write guard* after *The undo*: what Landlock is (a process restricts itself and every child, without privilege), the twelve write rights of ABI 3 that the rules handle and that reading, executing and the network stay open, a folder rule against a file rule (in place only: no rename, replace or delete), the minimum ABI 3 and its fault text, the checks before the first system call (fail closed, nothing restricted), that rulesets stack, and that the tests restrict child processes only. `docs/decisions.md` gets an entry *The write guard by the kernel: Landlock through ctypes*, dated 2026-10-18 (F0019-S0001), with the reasons of the feature's decisions 1 to 4 (the hook sees two tools, the kernel every route; `ctypes` over a binding; ABI 3's write set; fail closed) and the alternatives rejected (a binding from PyPI; chmod or ownership changes over the tree; a root helper).

## Smoke test

```bash
uv run -q python -c 'from factory.adapters.landlock import abi_version; print(abi_version() >= 3)'
```
Expect: `True`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/allowed" "$d/other"
uv run -q python -c '
import sys
from pathlib import Path
from factory.adapters.landlock import restrict_writes
base = Path(sys.argv[1])
restrict_writes([base / "allowed"], [])
for name in ("allowed/a.txt", "other/b.txt"):
    try:
        (base / name).write_text("x\n", encoding="utf-8")
        print(name, "written")
    except PermissionError:
        print(name, "refused")
' "$d"
```
Expect: two lines, `allowed/a.txt written` and then `other/b.txt refused`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python -c '
import sys
from pathlib import Path
from factory.adapters.landlock import restrict_writes
from factory.domain.errors import ConfinementError
base = Path(sys.argv[1])
try:
    restrict_writes([base / "missing"], [])
except ConfinementError as error:
    print(str(error).replace(str(base), "<d>"))
(base / "after.txt").write_text("x\n", encoding="utf-8")
print("still unrestricted")
' "$d"
```
Expect: two lines, `cannot open <d>/missing: No such file or directory` and then `still unrestricted`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: Format check: passed. Questions:

   1. The Interface says `restrict_writes` checks "folders before files, each in the given order" and raises at the first path that fails. No criterion tests that ordering. Criterion 4 gives each refusal one bad path at a time. Two coders could read the ordering two ways and both pass. Proposed new criterion, before the two closing ones: in a child process, `restrict_writes` raises the message of the first failing path. Rows: (a) a missing folder in `folders` and a missing file in `files` give the folder's message. (b) two missing folders give the first one's message. (c) two missing files give the first one's message. I would choose to add it.

   2. The Interface says a folder rule allows all twelve write rights beneath the folder. Criterion 3 shows only some of them: create file, make folder, delete file, append and truncate. Making a symbolic link inside A and renaming a file between two folders both under A are not shown. Rename is the `refer` right, and it is the only one of the twelve that crosses folders. Proposed: add two rows to criterion 3, "a symbolic link made in A is created" and "a file in A renamed to another folder in A succeeds". I would choose to add them. If you would rather leave the other rights untested, say so and I accept as is.

   Everything else is fine: the Interface is concrete, the smoke test is runnable with checkable Expect lines, the architecture fits (`domain` holds the constant, the fault text and the error; `adapters` holds `ctypes`) and the scope matches S0001 in `feature.md`.
4. 2026-10-18 human: 1. Yes: add the ordering criterion with its three rows (folder before file; first of two folders; first of two files), before the two closing criteria.
   2. Yes: add the two rows to criterion 3 (a symbolic link made in A is created; a file renamed between two folders under A succeeds). The rename row is the one that proves the refer right.
5. factory: started intake as self.
6. intake: accepted
   Carried in from journal entry 4 (the human's answers, not my improvements): criterion 3 gained two rows, "a symbolic link made in A is created" and "a file in A renamed to another folder in A succeeds"; a new criterion 9 holds the ordering rows (folder before file; first of two folders; first of two files). `make check` and `docs:` are now criteria 10 and 11, still last.
   - Interface: concrete modules and signatures (`factory.domain.confinement`, `factory.domain.errors.ConfinementError`, `factory.adapters.landlock`). The fault text, the constants, the system call numbers and every error message are exact.
   - Criteria: each is testable by one parametrized test or function. Every rule has both sides: the ABI fault and the pass (1), each refused input and its message (4), the ordering (9), empty rules (5), stacking (6), descriptors closed (7), `ConfinementError.detail` (8). The system-call failures are listed in the Interface as untestable, which is stated, not hidden.
   - Smoke test: the three commands are runnable. Each `Expect:` line is checkable against the output.
   - Architecture: the constant, the fault text and the error are in `domain`. The `ctypes` calls are in `adapters`. Nothing in `application` or `entry` is touched. No new dependency.
   - Scope: matches S0001 in `feature.md`. Nothing from "Out of scope" is touched.
7. factory: started tests as self.
8. tester: Wrote the tests from the Interface and the acceptance criteria. Every call of `restrict_writes`, including the ones expected to raise, runs in a child process (`sys.executable -c <code>`) on a tree under `tmp_path`. The `tree` fixture builds folders A (with subfolder d), B, O and P, the file F = P/f.txt, existing files in A and O, and two symbolic links (one to A, one to F). A refused write shows up in the child as `PermissionError` with errno 13. `abi_version` runs in-process as well as in a child.

   - criterion 1: tests/domain/test_confinement_abi.py::test_a_kernel_below_abi_3_has_a_fault (rows 0, 2, 3, 7)
   - criterion 2: tests/adapters/test_landlock.py::test_abi_version_reports_at_least_3_and_restricts_nothing
   - criterion 3: tests/adapters/test_landlock.py::test_a_restricted_process_writes_only_beneath_its_folders_and_on_its_files (15 rows, one child each)
   - criterion 4: tests/adapters/test_landlock.py::test_a_refused_path_raises_and_restricts_nothing (6 rows)
   - criterion 5: tests/adapters/test_landlock.py::test_empty_rules_refuse_every_write_and_leave_reading_open
   - criterion 6: tests/adapters/test_landlock.py::test_a_second_restriction_stacks_on_the_first (rows A, B)
   - criterion 7: tests/adapters/test_landlock.py::test_restricting_leaves_no_descriptor_open
   - criterion 8: tests/domain/test_confinement_abi.py::test_confinement_error_carries_its_detail_as_the_message
   - criterion 9: tests/adapters/test_landlock.py::test_the_first_failing_path_names_the_error (3 rows)
   - criteria 10 and 11 (`make check`, docs): no test; they belong to the coder and the documenter.

   Files created: tests/domain/test_confinement_abi.py, tests/adapters/test_landlock.py. No earlier test file was changed.

   The single `make test` run stopped at collection: neither test module could be imported, because `factory.domain.confinement`, `factory.domain.errors.ConfinementError` and `factory.adapters.landlock` do not exist yet. `make lint` is green after I wrapped two lines that were too long.

   How the criteria were written into tests:
   - In the criterion 3 row "F is opened for writing and truncated", the child opens F with `r+` and calls `truncate(0)`.
   - In the shell row, the child prints whether the exit status is non-zero and whether `O/c` exists; the test expects `True False`.
   - The criterion 4 and 9 tests replace the `tmp_path` root in the message with `<base>`, then compare the whole message.

   Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_confinement_abi.py - ImportError while importing test...
9. factory: started doing as self.
10. coder: Built the Landlock adapter, the minimum ABI and the error. The new tests pass and `make check` is green (`check: green`, total coverage 98.81 %).

    - `src/factory/domain/confinement.py` (new): `LANDLOCK_MINIMUM_ABI = 3` and `abi_fault(abi)`, with the fault text built from the constant.
    - `src/factory/domain/errors.py`: `ConfinementError(FactoryError)`. Its message is `detail` itself.
    - `src/factory/adapters/landlock.py` (new): `WRITE_RIGHTS`, `FILE_RIGHTS`, `abi_version()` and `restrict_writes(folders, files)`, built on `ctypes.CDLL(None, use_errno=True)` with `syscall` and `prctl`.
      - `_check_path` checks every path with `os.lstat` before the first system call, folders before files, each in the given order.
      - It then creates the ruleset (attribute `_RulesetAttr`, 8 bytes), adds one rule per path (`_PathBeneathAttr` with `_pack_ = 1`, 12 bytes; descriptor opened `O_PATH | O_CLOEXEC` and closed in a `finally`), sets `PR_SET_NO_NEW_PRIVS` and calls `landlock_restrict_self`.
      - An outer `finally` closes the ruleset's descriptor. `_raise_on_failure` turns a negative result into `ConfinementError("<call> failed: <strerror>")`.

    Main choice: every argument to the variadic `syscall` and `prctl` is passed as an explicit ctypes type (`c_long`, `c_int`, `c_uint32`, `c_size_t`, `c_void_p`, `c_ulong`). Rejected: passing bare Python ints. ctypes passes those as C `int`, which leaves the upper half of a 64-bit system-call argument undefined in a variadic call.

    Refactor: read the diff once and found nothing to change. The "cannot open" text is built twice: in `_check_path`, and in `_add_rule`'s guard for a path that vanishes between the check and the rule. Left as is.

    Noticed, not touched:
    - `landlock.py` shows 35 % in the coverage table. The tests call `restrict_writes` only in child processes, as the work item requires, and coverage does not measure children; the total stays above 90 %.
    - The failing system-call branches are uncovered; the Interface says no test can trigger them.
    - `make sast` passed on the ctypes use without any suppression marker.
    - The journal did not change what the task means, so the `## Description` stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 36 known, 3 gone
11. factory: started review as self.
12. reviewer: no findings

    I read `git diff main...HEAD -- . ':!factory'` (`src/factory/adapters/landlock.py`, `src/factory/domain/confinement.py`, `src/factory/domain/errors.py`, `tests/adapters/test_landlock.py`, `tests/domain/test_confinement_abi.py`) against the work item.

    - Acceptance criteria: each of criteria 1 to 9 has a test that checks what the criterion says. Criterion 3 has all 15 rows, each in its own child, including the symbolic-link row and the rename-within-A row the human added. Criterion 4 has 6 rows and checks that the child can still write in O afterwards. Criterion 9 has 3 rows for the ordering. The ABI limit is tested on both sides (2 and 3). Each rule's sides are rows of one parametrized test. Every `restrict_writes` call runs in a child process. The work item says which paths are left untested (the failing system calls, a negative `abi_version`) and why. The coder's journal entry 10 reports `check: green`.
    - Architecture: the domain module is pure (the constant and the fault text built from it). `ConfinementError` follows the `detail` pattern of the other errors. The adapter imports only `domain`. No command-line tool is called. No new dependency: the adapter uses the standard library's `ctypes`.
    - Implementation against the Interface: every path is checked with `os.lstat` before the first system call, folders before files, each in the given order. The ruleset attribute is 8 bytes. The rule struct is packed to 12 bytes, as the kernel declares it. Each rule's descriptor is opened `O_PATH | O_CLOEXEC` and closed in a `finally`, and the ruleset's descriptor in an outer `finally`. `PR_SET_NO_NEW_PRIVS` is set before `landlock_restrict_self`. Each failing call has the error text the Interface gives. `abi_version` turns a negative result into 0. Every argument to the variadic `syscall` and `prctl` is passed as an explicit ctypes type, which is correct.
    - Security: no shell or SQL is built from strings, and `src` has no suppression marker. The test's `# noqa: S603` on `subprocess.run` gives its reason beside it, as the existing tests do (`tests/test_layers.py:22`, `tests/domain/test_journal.py:398`).
    - Quality: `make duplicates` has 3 new findings. All are vulture's "unused function" for `abi_version`, `restrict_writes` and `abi_fault`, which is expected: the Description says nothing calls the adapter until S0002. The "cannot open" text appears in both `_check_path` and the `_add_rule` guard (for a path that disappears between the check and the rule). That is two lines with one meaning each, so I do not count it as duplicated logic.
    - Work item hygiene: the journal names the main choice (explicit ctypes argument types) and what was rejected (bare Python ints). The Description matches what was built. Criterion 11 (docs) still covers what the reader must know.

    Earlier tests: none. The diff only adds test files (`A` for both); it changes, renames or deletes no test file that `main` holds.
13. factory: started docs as self.
14. documenter: Wrote the documentation criterion 11 asks for. The code matches the Interface, so there are no findings.

    Files changed:
    - `docs/project-guide.md`: new section *The kernel's write guard* after *The undo*. It covers what Landlock is, the twelve write rights of ABI 3 with reading, executing and the network left open, and a folder rule against a file rule (in place only). It also covers the minimum ABI 3 and its fault text, the checks before the first system call (fail closed), stacking, and that the tests restrict child processes only. I also added a `ConfinementError(detail)` paragraph to *Errors*.
    - `docs/decisions.md`: new entry *The write guard by the kernel: Landlock through ctypes*, dated 2026-10-18 (F0019-S0001). It gives the reasons (the hook sees two tools, the kernel every route; `ctypes` over a binding; ABI 3's write set; fail closed) and the alternatives rejected (a PyPI binding; chmod or ownership changes over the tree; a root helper).

    I wrote no runnable examples, so I ran none. I changed only documents and did not run `make check`.

    Two sentences state a reason or an effect that the diff does not show. I wrote the reason for refusing symbolic links (a rule on a link would apply to its target) from my knowledge of how `O_PATH` opens work. I wrote the file rule's "nothing can be renamed onto it" from how Landlock treats rename rights. The tests do not cover either. Both are in the project guide, and the reviewer can cut them if they read as unverified.

    Cross-read and found current against the diff: `README.md`, `docs/operator-guide.md`, and the *guard command*, *undo* and *claude -p runtime* sections of the project guide. The new adapter is not wired in, so none of them describes anything that changed.

    Stale text noticed and not touched: none.

    `check`: check: green
    `documents`: documents ok
15. factory: started smoke-test as self.
16. smoke-tester: Smoke test passed: all three commands met their `Expect:` lines. No findings.

    I ran each command under `## Smoke test` from the repository root, exactly as written, each in its own shell. The `trap` in commands 2 and 3 removed their temporary folders. I added `; echo "exit=$?"` after each command only to record its exit status; the commands themselves were not changed.

    Command 1 (`abi_version() >= 3`):
    ```
    True
    exit=0
    ```
    Met `Expect: True`.

    Command 2 (`restrict_writes([allowed], [])`, then a write in `allowed` and one in `other`):
    ```
    allowed/a.txt written
    other/b.txt refused
    exit=0
    ```
    Met `Expect:` (two lines: `allowed/a.txt written`, then `other/b.txt refused`).

    Command 3 (`restrict_writes([missing], [])`, then a write in the base folder):
    ```
    cannot open <d>/missing: No such file or directory
    still unrestricted
    exit=0
    ```
    Met `Expect:` (two lines: `cannot open <d>/missing: No such file or directory`, then `still unrestricted`).

    Checked against the acceptance criteria: nothing in the output contradicts any of them.
    - Command 1 fits criterion 2 (ABI of at least 3 on this machine).
    - Command 2 fits criteria 3 and 5: a write beneath the allowed folder succeeds, a write elsewhere fails with `PermissionError`.
    - Command 3 fits criterion 4: the exact message for a missing folder, and nothing is restricted after the refusal.

    Not covered by the smoke test, and not run by me: criteria 6, 7 and 9 (stacking, closed descriptors, ordering), the file-rule rows of criterion 3, and criteria 10 and 11 (`make check`, docs). For these I rely on the earlier stages' entries: the tests named in entry 8, and `check: green` in entries 10 and 14.

    Open: nothing.
17. factory: done (pull request merged); cost: 7 runs, 6.4 min, 45 turns, 212146 tokens in (599240 more from cache), 27079 out, $1.94
