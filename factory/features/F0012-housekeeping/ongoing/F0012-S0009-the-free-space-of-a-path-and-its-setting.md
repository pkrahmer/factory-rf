---
stage: ready
pr: null
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
