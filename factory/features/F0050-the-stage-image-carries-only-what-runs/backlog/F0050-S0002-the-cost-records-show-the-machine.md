# The cost records show the image sizes, the free disk and the memory peak

## Description

The growth that F0050 removes came as a surprise: nothing the factory writes says how large its images are, how much disk is left, or how much memory the containers took. On 2026-11-04 factory-vm held a 2.4 GB image of an idle instance, a stage image that was two thirds leftovers, and a memory peak of 8.1 GB of 15.6 GB, and each was found only by hand. This story adds six measures to every completed cost record, so that the records on GitHub and the Factory Timeline show them from a distance: the sizes of the base image and of the project's layer, the free space of the machine's image store and of the stage's dataset, and the memory peak and total. The memory peak is the kernel's high-water mark of the cgroup that holds the factory user's containers, which cannot be reset on the kernels in use (6.8 on factory-vm): it is the highest use since that cgroup began, on a VM with lingering since boot, not the peak of the run. Its name says so. The first record in which it rises names the run that raised it. A measure the machine cannot give is `None`, as every other unknown measure of the record is. The factory's log gets the sizes in its line for each built image.

## Interface

- `CostRecord` (`factory.domain.cost_records`) gets six optional fields, each a `NonNegativeInt` or `None`, and, like the other measures, `None` on a `started` record:
  - `base_image_bytes`: the size of the base image (`FACTORY_STAGE_IMAGE`) the run's image was built on;
  - `project_layer_bytes`: the project image's size minus the base's; `0` when the project has no stage file;
  - `store_free_bytes`: the free space of the file system that holds podman's image store;
  - `dataset_free_bytes`: the free space of the stage's dataset (`FACTORY_WORKSPACE`), which on ZFS respects the dataset's quota;
  - `memory_peak_since_boot_bytes`: `memory.peak` of the cgroup v2 slice of the user that runs the containers (`/sys/fs/cgroup/user.slice/user-<uid>.slice/memory.peak`);
  - `memory_total_bytes`: the machine's memory (`MemTotal`).
- The two image sizes are measured when the factory builds or adopts an image (at start and after a changed stage file, F0049), not at every run; the other four when the record is completed. The coder decides through which interface each is read, within the wrappers rule; the existing disk-space interface serves the free space.
- The records contract moves from `4.1` to `4.2` (added optional fields), and its schemas are regenerated with `uv run python -m factory.entry.contract`.
- The log line of a built project image becomes `stage image: built <identity> at <commit> in <s> s, base <GB> GB, layer <GB> GB` (two decimals); the factory's start writes one line `stage image: base <GB> GB` for an instance without a stage file.

## Acceptance criteria

1. A completed record carries the six fields; a `started` record that carries any of them is refused, as for the other measures. Rows: each field at `0`, at a large value, and at `-1` (refused).
2. A measure that cannot be read (no such cgroup file, an image inspect without a size, a file system that cannot be read) is `None` on the record and does not fail the run or stop the factory.
3. `project_layer_bytes` is `0` for a project without a stage file and the difference of the two sizes for one with it; the two image sizes change only after a build or a return to the base.
4. `memory_peak_since_boot_bytes` is the value read from the slice's `memory.peak` when the record is completed; a later record with a higher file value carries the higher value.
5. The records contract is `4.2`, and its schemas match the models.
6. The two log lines have the form of the Interface.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`: in the section on cost records, the six fields, what each measures, and that the memory peak is a high-water mark since the slice began (since boot on a VM with lingering), not the run's own peak; in *The project's stage file*, the new log lines. `docs/decisions.md`: one entry that the records carry the machine's measures and why the peak is the slice's high-water mark (no reset before kernel 6.12, and sampling during a run was not worth its cost). `README.md` and the project guide: none.

## Smoke test

```bash
grep -cE '^RECORDS_CONTRACT = "4\.2"$' src/factory/domain/contract.py
grep -oE 'base_image_bytes|project_layer_bytes|store_free_bytes|dataset_free_bytes|memory_peak_since_boot_bytes|memory_total_bytes' src/factory/domain/cost_records.py | sort -u | wc -l
uv run pytest tests/domain -q 2>&1 | tail -1
```

Expect: `1`, `6`, then a line that ends in `passed` with no `failed`.

## Journal
