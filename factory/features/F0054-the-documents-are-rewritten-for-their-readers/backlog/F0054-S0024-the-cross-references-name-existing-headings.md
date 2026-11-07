# The cross-references between pages name the headings that exist

<!-- proposed by feature acceptance of 2026-11-07; refine before starting -->

## Description

Four references from one page to a section of another name a heading that does not stand in the target page as written, so a reader who searches the target for it finds nothing. `docs/operator-guide/install.md:121` sends the reader to *In a job* in `machine.md`, which is a bold paragraph under the heading *The idle shutdown*, not a heading. `docs/operator-guide/work-items.md:66` names "What a work item cost" in `records.md`, whose heading is *What a work item cost: `factory-bill`*. `docs/project-guide/machine.md:487` names *`StageFinisher.finish`* in `pipeline.md`, whose heading is *`StageFinisher.finish(aftermath)`*. `docs/operator-guide/agent-runtime.md:407` names "The stage environment" under *Configuration* in `install.md`, a bold paragraph that now stands under *Reference*. This story corrects each of the four references so that it names the heading as the target page writes it, or the paragraph and the heading it stands under, as `docs/operator-guide/stops.md:53` already does for *In a job*. No other sentence changes, no heading is renamed, and the check of references between pages is left to a later feature. The story takes the docs route.

## Interface

- `docs/operator-guide/install.md`, `docs/operator-guide/work-items.md`, `docs/operator-guide/agent-runtime.md` and `docs/project-guide/machine.md`: the one reference each named in the Description, corrected as described there.
- No heading of any page changes, so no other link changes with it.
- `docs/checked-documents.txt` stays unchanged: all four pages are on it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/install.md` no longer names *In a job* as a heading of `machine.md`; its reference names *The idle shutdown* in `machine.md`, with or without the paragraph *In a job* under it.
2. `docs/operator-guide/work-items.md` names the heading of `records.md` as it stands, *What a work item cost: `factory-bill`*, or links to it so that the reader reaches it.
3. `docs/project-guide/machine.md` names the heading of `pipeline.md` as it stands, *`StageFinisher.finish(aftermath)`*.
4. `docs/operator-guide/agent-runtime.md` names *The stage environment* as a paragraph under *Reference* in `install.md`, not under *Configuration*.
5. Every reference of the form *heading* in [page](page.md) or "heading" in [page](page.md) in the files of `docs/checked-documents.txt` names a heading of its target page exactly, its code marks aside; the reviewer checks this by script and quotes the script's empty output. Before this story the script lists the four references above; after it, none.
6. `make documents` prints `documents ok` and no finding for the four pages.
7. `make check` stays green.
8. docs: the four pages as criteria 1 to 5; the reader reaches each section another page sends them to. `docs/decisions.md`: none.

## Smoke test

```sh
grep -c 'In a job\* in \[machine.md\]' docs/operator-guide/install.md
```
Expect: `0`

```sh
grep -c '"What a work item cost" in' docs/operator-guide/work-items.md
```
Expect: `0`

```sh
grep -c 'StageFinisher.finish`\* in' docs/project-guide/machine.md
```
Expect: `0`

```sh
grep -c '"The stage environment" under \*Configuration\*' docs/operator-guide/agent-runtime.md
```
Expect: `0`

```sh
make documents 2>&1 | tail -1 | cut -d' ' -f1-2
```
Expect: `documents ok`

## Journal
