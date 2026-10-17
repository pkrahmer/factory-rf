---
stage: done
pr: 161
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The free space of a path, and its setting

## Assignment (as of log entry 1)

On 2026-10-16 the host's drive ran full while the container's `df` showed 860 GB free, and `docker exec` hung for four hours: nothing in the container could see the host's limit, and nothing in the factory looked at the disk at all. The human's word ("Disk space, fixed in v1.1") is a machine stop for low disk space, an operator guide that says what the container cannot see, and a disk record at each major change. This story builds what those need and changes no behaviour yet: an interface that tells the free and the used bytes of a path, its implementation with the standard library, the setting `FACTORY_MIN_FREE_GB` (default 5), the text of a low-disk fault, and the wiring that puts the interface into the boundaries. F0012-S0010 raises the stop with it at every tick, F0012-S0016 records the disk with it.

## Interface

`src/factory/application/machine.py` gains:

```python
class DiskSpace(ABC):
    """Tells how much room the file systems have and how much a folder takes."""

    @abstractmethod
    def free_bytes(self, path: Path) -> int:
        """The bytes an unprivileged user may still write on the file system of `path`; `OSError` when it cannot be read."""

    @abstractmethod
    def used_bytes(self, path: Path) -> int:
        """The sizes of the regular files under `path`, symbolic links and other non-regular files skipped; 0 for a missing path."""
```

`src/factory/adapters/disk_space.py` (new): `class ShutilDiskSpace(DiskSpace)`. `free_bytes` is `shutil.disk_usage(path).free`, which raises `FileNotFoundError` for a missing path. `used_bytes` walks `path` without following symbolic links and adds the size of every regular file; a symbolic link (to a file or to a folder) adds nothing, and neither does a file of another kind (a named pipe, which it does not open); it returns 0 when `path` does not exist.

`src/factory/application/boundaries.py`: `Boundaries` gains a last, optional field `disk: DiskSpace | None = None`, after `settings`, so every construction written before it stays valid.

`src/factory/domain/settings.py`: `MIN_FREE_SPACE_VARIABLE = "FACTORY_MIN_FREE_GB"`, `DEFAULT_MIN_FREE_GB = 5`, and `InstanceSettings.min_free_gb: PositiveInt = DEFAULT_MIN_FREE_GB`. `read_settings` reads the variable: unset or blank gives 5; a value that, stripped, is ASCII digits only and at least 1 gives that number; anything else raises `SettingsInvalid(MIN_FREE_SPACE_VARIABLE, "is not a whole number of gigabytes of at least 1")`.

`src/factory/domain/disk.py` (new):

```python
GIGABYTE = 10**9

def gigabytes(byte_count: int) -> str:
    """`byte_count` in gigabytes of 10**9 bytes, rounded down to one decimal: `3.2`."""

def disk_low_detail(free: Mapping[Path, int], minimum_gb: int) -> str | None:
    """The fault of the paths with less than `minimum_gb` gigabytes free, None when all have enough."""
```

`disk_low_detail` names each path with less than `minimum_gb * GIGABYTE` bytes free, in the mapping's order, as `<path> has <gigabytes> GB free, less than the <minimum_gb> GB FACTORY_MIN_FREE_GB asks for`, joined by `; `. Exactly `minimum_gb * GIGABYTE` bytes is enough.

`src/factory/entry/wiring.py`: `build_boundaries` sets `disk=ShutilDiskSpace()`.

Tests: `tests/domain/test_disk.py` (criteria 1 and 2), `tests/adapters/test_disk_space.py` (criteria 3 and 4), `tests/domain/test_settings_min_free.py` (criteria 5 and 6), a new test function in `tests/entry/test_wiring_boundaries.py` with that module's `settings` fixture and `FakeHostingService` as `hosting` (criterion 7), and `tests/application/test_disk_space_interface.py` (criterion 8). No existing test changes.

## Acceptance criteria

1. `gigabytes` gives `0.0` for 0, `0.9` for 999_999_999, `1.0` for 1_000_000_000, `3.2` for 3_299_999_999 and `812.3` for 812_345_678_901. Rows of one parametrized test.
2. `disk_low_detail({Path("/work"): 5 * GIGABYTE}, 5)` is `None`; with `5 * GIGABYTE - 1` it is `/work has 4.9 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for`; with `/work` and `/state` both at `1_200_000_000` it names `/work` then `/state`, joined by `; `; with `/work` low and `/state` at 6 GB it names `/work` only. Rows of one parametrized test.
3. `ShutilDiskSpace().free_bytes(tmp_path)` is positive and at most `shutil.disk_usage(tmp_path).total`; for a missing path it raises `FileNotFoundError`.
4. `ShutilDiskSpace().used_bytes` of a folder holding files of 3 and 5 bytes and a subfolder with a file of 7 bytes is 15; in that folder, a symbolic link to a file of 100 bytes outside it, a symbolic link to a folder outside it that holds a file of 100 bytes, and a named pipe (`os.mkfifo`) each add nothing; a missing path gives 0. Rows of one parametrized test.
5. `read_settings` gives `min_free_gb == 5` when `FACTORY_MIN_FREE_GB` is unset or blank, 1 for `1`, 12 for ` 12 `; it raises `SettingsInvalid` with `variable == "FACTORY_MIN_FREE_GB"` and `fault == "is not a whole number of gigabytes of at least 1"` for `0`, `-1`, `2.5`, `five` and `"٣"` (an Arabic-Indic digit). Rows of one parametrized test.
6. `InstanceSettings` built without `min_free_gb` has `min_free_gb == 5`; with `min_free_gb=1` it is accepted; with `min_free_gb=0` it is refused with `pydantic.ValidationError`. Rows of one parametrized test, the model built through a variable typed `type[BaseModel]`.
7. `build_boundaries` gives boundaries whose `disk` is a `ShutilDiskSpace`; `Boundaries` built without `disk` has `disk is None`.
8. `DiskSpace` is an abstract base class whose abstract methods are exactly `free_bytes` and `used_bytes`, and `ShutilDiskSpace` derives from it.
9. `make check` stays green.
10. docs: the operator guide's settings table gets the row `FACTORY_MIN_FREE_GB` (optional, whole gigabytes of 10^9 bytes, at least 1, default 5; what it guards comes with the low-disk stop). Its section *The machine's image* says what the container cannot see: under Docker Desktop's WSL 2 backend there is no disk limit, so `df` inside the container shows the virtual disk (about 1 TB) and a check of free space inside it fires only on a Linux host or with a real limit; under Docker Desktop the host drive is watched from outside, Docker's disk image belongs on a drive with room, and the space comes back with `fstrim -v /mnt/docker-desktop-disk` in the `docker-desktop` distribution followed by `compact vdisk` in `diskpart` with Docker stopped. The project guide names `DiskSpace` and `ShutilDiskSpace` where it lists the machine's interfaces (the clock, the factory log, the health status store). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from pathlib import Path
from factory.adapters.disk_space import ShutilDiskSpace
from factory.domain.disk import GIGABYTE, disk_low_detail, gigabytes
print(ShutilDiskSpace().free_bytes(Path('.')) > 0, gigabytes(3_299_999_999))
print(disk_low_detail({Path('/work'): 5 * GIGABYTE - 1, Path('/state'): 9 * GIGABYTE}, 5))
"
```
Expect: two lines: `True 3.2` and `/work has 4.9 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for`.

```bash
uv run python -c "
from factory.domain.settings import read_settings
print(read_settings({'FACTORY_REPOSITORY_URL': 'https://github.com/o/r.git', 'FACTORY_INSTANCE': 'factory-1'}).min_free_gb)
"
```
Expect: `5`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures: `DiskSpace` in `application/machine.py`, `ShutilDiskSpace` in `adapters/disk_space.py`, `Boundaries.disk` as an optional last field, `MIN_FREE_SPACE_VARIABLE`, `DEFAULT_MIN_FREE_GB` and `InstanceSettings.min_free_gb` in `domain/settings.py`, and `gigabytes` and `disk_low_detail` in `domain/disk.py`. The wiring change is stated. I did not open the existing source files to confirm the named modules; I judged the story text only.
   - Criteria: each is testable by one test function, as rows of a parametrized test where the story says so. Each behaviour the Interface states has a criterion. The conversion and its rounding down are in 1 (999_999_999 gives 0.9). The fault text, its order, the join and the exact-minimum boundary are in 2. The free-space error is in 3. Which files count, skipped links and pipes, and the missing path are in 4. The default, blank, stripped and ASCII-only parsing are in 5. The default and limit of the model field are in 6. The wiring and the `None` default are in 7. The abstract class and its subclass are in 8. Each rule has both sides: the setting accepts 1 and 12 and refuses 0, -1, 2.5, `five` and `"٣"`; `min_free_gb` accepts 1 and refuses 0; the detail is `None` at exactly the minimum and a fault one byte below it.
   - Demo: both blocks are runnable `uv run python -c` commands, and each `Expect:` line gives output that can be compared exactly.
   - Architecture: the interface sits in application, the implementation in adapters, the pure text rules in domain, and the wiring in entry, so the layering holds. The interface is an ABC with the implementation inheriting it. The Interface also states the Tests and the docs criterion.
   - Scope: the story builds only the interface, the setting, the fault text and the wiring. It changes no behaviour, and the stop is left to S0010 and the disk record to S0016, matching FEATURE.md scope 1.4 and decision 20. Nothing in the story falls under Out of scope.
3. tester: Wrote red tests for criteria 1–8, one test function per criterion. The rows are the cases the criteria and the Interface name.
   - criterion 1: tests/domain/test_disk.py::test_gigabytes_are_rounded_down_to_one_decimal (5 rows: 0, 999_999_999, 1e9, 3_299_999_999, 812_345_678_901)
   - criterion 2: tests/domain/test_disk.py::test_the_disk_low_detail_names_each_path_below_the_minimum (rows: exactly the minimum gives None, one byte below, both low in mapping order joined by `; `, one low and one at 6 GB)
   - criterion 3: tests/adapters/test_disk_space.py::test_the_free_bytes_are_positive_and_within_the_total_or_missing_raises
   - criterion 4: tests/adapters/test_disk_space.py::test_the_used_bytes_add_the_regular_files_only. Rows: plain files 3+5+7=15; adding a link to a 100-byte file, a link to a folder holding a 100-byte file, or an `os.mkfifo` pipe still gives 15; a missing path gives 0.
   - criterion 5: tests/domain/test_settings_min_free.py::test_the_minimum_free_space_is_read_or_refused. Rows: unset, empty or blank gives 5; `1` gives 1; ` 12 ` gives 12; `0`, `-1`, `2.5`, `five` and `"٣"` each raise SettingsInvalid with that variable and fault.
   - criterion 6: tests/domain/test_settings_min_free.py::test_the_settings_keep_a_minimum_free_space_of_at_least_one (rows: default 5, 1 accepted, 0 gives ValidationError; built through a variable typed `type[BaseModel]`)
   - criterion 7: tests/entry/test_wiring_boundaries.py::test_the_built_boundaries_read_the_disk_and_boundaries_without_one_have_none. It uses the module's `settings` fixture and `FakeHostingService` as hosting. The second half rebuilds `Boundaries` from the built fields minus `disk` (via `dataclasses.fields`) and checks that `disk is None`.
   - criterion 8: tests/application/test_disk_space_interface.py::test_disk_space_is_an_abstract_base_class_with_two_operations_and_one_implementation. It checks `issubclass(DiskSpace, ABC)`, that `__abstractmethods__` is exactly {free_bytes, used_bytes}, and that ShutilDiskSpace derives from DiskSpace.

   New files: tests/domain/test_disk.py, tests/adapters/test_disk_space.py, tests/domain/test_settings_min_free.py, tests/application/test_disk_space_interface.py. Changed file: tests/entry/test_wiring_boundaries.py, which gains one function and imports of `fields`, `ShutilDiskSpace` and `Boundaries`. No existing test function changed.

   `make test` fails as intended. These modules and names could not be imported: `factory.domain.disk`, `factory.adapters.disk_space` and `DiskSpace` from `factory.application.machine`. Because of that, all of test_wiring_boundaries.py fails to collect until the adapter exists. The settings tests fail because `min_free_gb` and the variable don't exist yet. `make lint` is green. I skipped the type check as the stage says.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/entry/test_wiring_boundaries.py - ImportError while importing tes...
4. coder: Built the disk-space interface, its standard-library implementation, the `FACTORY_MIN_FREE_GB` setting, the low-disk fault text and the wiring. Behaviour is unchanged. `make check` is green and the tests are untouched.
      - `src/factory/application/machine.py`: `DiskSpace(ABC)` with `free_bytes` and `used_bytes`. Each docstring is wrapped over two lines to fit the line length.
      - `src/factory/adapters/disk_space.py` (new): `ShutilDiskSpace(DiskSpace)`. `free_bytes` is `shutil.disk_usage(path).free`. `used_bytes` uses `os.walk(followlinks=False)` and calls `lstat` on each entry, adding the size only when `S_ISREG` holds. Links and named pipes are therefore never followed or opened. `os.walk` yields nothing for a missing path, so that gives 0.
      - `src/factory/application/boundaries.py`: `disk: DiskSpace | None = None` is added after `settings`. The existing "last and optional" comment now covers both fields.
      - `src/factory/domain/settings.py`: adds `MIN_FREE_SPACE_VARIABLE`, `DEFAULT_MIN_FREE_GB`, `InstanceSettings.min_free_gb: PositiveInt` and `_min_free_gb`. `_min_free_gb` requires `isascii() and isdigit()`, because `isdigit` alone accepts Arabic-Indic digits.
      - `src/factory/domain/disk.py` (new): `GIGABYTE`, plus `gigabytes` and `disk_low_detail`. `gigabytes` rounds down using integer tenths (`byte_count * 10 // GIGABYTE`). `disk_low_detail` takes the variable name from `MIN_FREE_SPACE_VARIABLE`.
      - `src/factory/entry/wiring.py`: `build_boundaries` sets `disk=ShutilDiskSpace()`.
      - Commits: ee2d3f4 (feat) and c166bb7 (refactor, the comment wording only). Reading my own diff found nothing else to change.
      - Main decision: `gigabytes` uses integer arithmetic rather than float formatting. I rejected `f"{x / GIGABYTE:.1f}"` because it rounds to nearest (999_999_999 would give `1.0`), and `math.floor` on a float can be off at the boundaries.
      - Rejected: `Path.rglob` with `is_file()` for `used_bytes`. `is_file()` follows symbolic links, so linked files would be counted.
      - Both demo blocks print the expected output.
      - Noticed but not touched: `make duplicates` reports 7 new dead-code findings (`free_bytes`, `used_bytes`, `Boundaries.disk`, `disk_low_detail`, `min_free_gb`). These are expected until the low-disk stop (S0010) and the disk record (S0016) use them. `used_bytes` lets a `FileNotFoundError` from a file removed during the walk propagate; neither the Interface nor any criterion says what should happen in that case.
      - Open: the docs criterion (10) is for the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 7 new, 39 known, 0 gone
5. reviewer: no findings.
      - Acceptance criteria: I read each of criteria 1–8 against its test, and each test checks what its criterion says. `tests/domain/test_disk.py` has 5 `gigabytes` rows and 4 `disk_low_detail` rows; the exact minimum gives None and one byte below gives the fault. `tests/adapters/test_disk_space.py` covers `free_bytes` within the total and a missing path raising `FileNotFoundError`. It also covers `used_bytes` with files only, a link to a file, a link to a folder, a named pipe and a missing path. `tests/domain/test_settings_min_free.py` covers unset, empty, blank, 1, ` 12 `, 0, -1, 2.5, `five` and `٣`, plus the model's default, 1 and 0 through `type[BaseModel]`. `tests/entry/test_wiring_boundaries.py` checks `disk` as built and `None` when left out. `tests/application/test_disk_space_interface.py` checks the abstract methods and the subclass. Both sides of every stated limit are tested: `PositiveInt` at 0 and 1, the setting at 0 and 1, and the minimum at exactly and one byte below. No existing test function changed. The coder's entry records `check: green`.
      - Architecture: `DiskSpace` is an ABC in `application/machine.py` whose method bodies are docstrings only. `ShutilDiskSpace` in `adapters/disk_space.py` inherits it and uses the standard library only, with no command-line tool. The pure text rules are in `domain/disk.py`, which imports only `domain/settings`. The wiring is only in `entry/wiring.py`. `Boundaries.disk` is the last optional field, as the Interface states.
      - Implementation, checked against the Interface: `os.walk(followlinks=False)` puts links to folders among the folders and does not descend into them. `lstat` with `S_ISREG` skips links to files and pipes without opening them, and a missing path yields nothing, so it gives 0. `_min_free_gb` uses the shared `_optional`, which strips, and requires ASCII digits. `gigabytes` uses integer tenths, so it rounds down exactly.
      - Security: no shell, SQL, secrets or suppression markers. The input check is at the settings boundary.
      - Quality: I searched `src/factory` and found no existing helper for the same parsing, size walk or GB formatting. The `@override` methods without docstrings follow the existing adapters' style (`adapters/clock.py`). The comments explain why. The 7 new `make duplicates` dead-code findings are the parts S0010 and S0016 will use, as the coder's entry says.
      - Ticket hygiene: the log gives the main decision (integer tenths rather than float formatting) and what was rejected (`rglob` with `is_file`, which follows links). `Assignment` matches what was built, and criterion 10 still describes the docs to write.
      - Open, not a finding: if a file is removed during the walk, `used_bytes` passes on its `FileNotFoundError`. The Interface does not cover this; S0016, which calls `used_bytes`, may need to decide it.
6. documenter: Wrote the docs for criterion 10. I ran no `make check`, because only documents changed. `python -m factory.entry.check_documents` prints `documents ok`.
   - `docs/operator-guide.md`, settings table: new row `FACTORY_MIN_FREE_GB`. It is optional, in whole gigabytes of 10^9 bytes, at least 1, default 5, and unset or blank gives the default. Bad values are refused with the variable named. The row says what it guards "comes with the low-disk stop".
   - `docs/operator-guide.md`, new subsection "What the container cannot see" at the start of *The machine's image*. Under Docker Desktop's WSL 2 backend there is no disk limit, so `df` inside the container shows the virtual disk (about 1 TB). A free-space check inside the container therefore fires only on a Linux host or with a real limit. The host drive is watched from outside, and Docker's disk image belongs on a drive with room. To get the space back: `fstrim -v /mnt/docker-desktop-disk` in the `docker-desktop` distribution, then `compact vdisk` in `diskpart` with Docker stopped.
   - `docs/project-guide.md`, where the machine's interfaces are listed: `DiskSpace` (`free_bytes`, `used_bytes`) and `ShutilDiskSpace` in `factory.adapters.disk_space`. It also says `Boundaries.disk` is optional and set by `build_boundaries`.
   - Cross-read against the diff and found current: README, the operator guide's description of `read_settings` and of the boundaries, and the project guide's `build_boundaries` paragraph. That paragraph lists what is built and now has `disk` missing, but it is not a full list, so I left it. The `boundaries` test-fixture paragraph is unaffected, because `disk` is optional.
   - No findings for the coder. The code matches the Interface and every public name has its docstring.
   - Not touched: `used_bytes` lets a `FileNotFoundError` through when a file disappears during the walk. This is already open in the log, for S0016 to decide.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands ran from the repository root and met their `Expect:` lines. No findings.

   Command 1 (free space, `gigabytes`, `disk_low_detail`):
   ```
   True 3.2
   /work has 4.9 GB free, less than the 5 GB FACTORY_MIN_FREE_GB asks for
   ```
   Met: the expected two lines match exactly. `/state` at 9 GB is left out of the fault, as criterion 2 requires for a path with enough room.

   Command 2 (`read_settings` without `FACTORY_MIN_FREE_GB`):
   ```
   5
   ```
   Met: the default is 5, as criterion 5 says.

   Against the acceptance criteria: the output agrees with criteria 1 (3_299_999_999 rounds down to 3.2), 2 (one byte below the minimum gives the fault text, a path above it is not named), 3 (`free_bytes` of an existing path is positive) and 5 (unset gives 5). Nothing in the demo contradicts criteria 4 and 6–10. The commands did not exercise those, and the log records their tests and docs.
8. done (pull request merged); cost: 6 runs, 5.2 min, 40 turns, 196k tokens in (666k more from cache), 20k out, $1.30
