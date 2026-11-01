# The operator guide and the decision log agree with copy snapshots and the job
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

The feature acceptance F0047-A0001 found three places where the documents say less than, or the opposite of, what F0047 built:

- **Copy snapshots.** The operator guide still says the stage environment is one ("every stage runs on a ZFS dataset"). It calls `FACTORY_WORKSPACE` "the dataset's mount point" and gives the missing-variable order of `zfs` alone. Since S0001, `FACTORY_SNAPSHOTS=copy` runs stages on a plain directory with a copied base, and with `copy` the base is named first.
- **An old decision not marked.** The decision *Every tool of the machine's image is pinned, and its identity is generated at build* (2026-10-16) still says "the eight Debian tools by `name=version`" and has no bullet that S0006's *Debian's packages follow the base image's release* changed it. The log marks such entries with a `Superseded in part by` bullet.
- **The token's folder in a job.** *On Cloud Run* mounts the hosting token from Secret Manager at `/secrets/hosting-token`, but does not say that the preflight's `token-file` item requires the token's folder to belong to the factory's user (root in a job) with no permission bit for group or others, nor what the operator sees when the mount does not meet it.

This story corrects the documents only. Unchanged: all code, every test, `vm/`, and the rule of the `token-file` item. Whether Cloud Run's secret mount meets that rule is unmeasured and stays the human's; the text states the rule and the item's sentence, not a measurement.

## Interface

No module under `src/factory/` changes, and no test changes. The documenter changes `docs/operator-guide.md` and `docs/decisions.md`. No tester work: the criteria are the text the documenter writes, read by the review and by `make documents`.

## Acceptance criteria

1. `docs/operator-guide.md`, the paragraph **The stage environment.** (today "There is one: every stage runs on a ZFS dataset ...") names both kinds of snapshots: a ZFS dataset by default, and with `FACTORY_SNAPSHOTS=copy` a plain directory with a copied base (pointing to *Without ZFS*). It no longer says "There is one".
2. The configuration table: `FACTORY_WORKSPACE` is "the folder the stage containers mount at `/work`: the dataset's mount point with `zfs`, a plain directory with `copy`"; `FACTORY_DATASET` is required "with `zfs`"; and the missing-variable order is given for both (`zfs`: the dataset, the workspace, the image; `copy`: the base, the workspace, the image), as `build_boundaries` raises them.
3. `docs/decisions.md`, the entry *Every tool of the machine's image is pinned, and its identity is generated at build*, gains a bullet `Superseded in part by "Debian's packages follow the base image's release"`: the Debian packages of the stage image now follow the base image's release; the base image's digest, `uv`, Claude Code and opencode keep their pins.
4. `docs/operator-guide.md`, *On Cloud Run*, *What the job needs*, the bullet **Secrets are files** says that the hosting token's folder is checked by the `token-file` item (owner the factory's user, root in a job; no bit for group or others). It quotes the item's sentences `the folder <folder> belongs to uid <n>, not to <m>` and `the folder <folder> has mode <mode>; make it 0700`, and refers to *The hosting-service token*.
5. `make documents` prints `documents ok`.
6. `make check` stays green.
7. docs: the four changes of criteria 1 to 4, in `docs/operator-guide.md` and `docs/decisions.md`; the project guide and `README.md`: none, because neither describes the stage environment's kinds or the token's folder.

## Smoke test

```bash
grep -c 'There is one: every stage runs on a ZFS dataset' docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'Superseded in part by "Debian.s packages follow the base image.s release"' docs/decisions.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: one line, `documents ok`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
