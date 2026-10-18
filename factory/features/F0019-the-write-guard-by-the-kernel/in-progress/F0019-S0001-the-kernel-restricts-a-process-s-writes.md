---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 220
comments_read: [6251100326]
handed_over: null
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
