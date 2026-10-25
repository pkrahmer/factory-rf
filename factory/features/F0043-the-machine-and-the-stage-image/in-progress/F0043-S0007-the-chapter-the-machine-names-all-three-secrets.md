---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-25T08:23:26.940839Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T08:23:26.935345Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T08:23:26.940839Z'
  stage: intake
---

# The chapter "The machine" names all three secrets in every place

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

The operator guide's chapter `## The machine` disagrees with itself on which secrets the VM needs. *On GCP, step by step*, step 8, and decision 10 of `feature.md` say that all three files must exist in `/home/factory/.secrets` (`hosting-token`, `claude-token`, `anthropic-api-key`), because `vm/setup.sh` writes all three paths into `factory.env`, the factory mounts every login file that is set (`login_paths` in `factory.adapters.agent_launch`), and podman refuses to mount a missing file (exit status 125). But *The script*, "The two passes", tells the operator to place "the token, and the login file for your runtime (`claude-token` or `anthropic-api-key`)". An operator who follows that section and places two files gets agent runs that stop at podman's mount. Step 8 itself gives the wrong reason: it says "An empty `anthropic-api-key` means no key: podman refuses to mount a missing file". The emptiness rule and the missing-file rule are two separate facts, and that sentence joins them with "because". The chapter's *The stage image* also sends the operator to *Update the pins* under "The machine's image" for `vm/Dockerfile`. That list names eight Debian packages including `sudo`, but `vm/Dockerfile` has seven and no `sudo`, so an operator who follows it looks for a pin that is not there. This story corrects those three passages. Nothing else in the chapter changes. What stays: every other sentence of the chapter, `vm/setup.sh`, and the code. The chapter of v1.1's image, which F0044 (the layers go) removes, stays too.

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md` only. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/operator-guide.md`, chapter `## The machine`; the smoke test and `make documents` check these, and no test does:
   - "The two passes" (under *The script*) tells the operator to place all three files, `hosting-token`, `claude-token` and `anthropic-api-key`, in `/home/factory/.secrets`. It says that all three must exist whatever the runtime, and that the key file stays empty with the `claude` runtime. It no longer contains the words "the login file for your runtime".
   - *On GCP, step by step*, step 8, gives the two facts as two sentences. First: all three files must exist, because the factory mounts every login file the environment file names and podman refuses to mount a missing one (exit status 125). Second: an empty `anthropic-api-key` means no key. It no longer contains "means no key: podman".
   - *The stage image* names the seven Debian packages of `vm/Dockerfile` (`git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs`, `npm`). It says that `sudo` is pinned in `image/Dockerfile` alone, and that a changed pin is checked with `uv run pytest tests/test_stage_image.py tests/test_image.py`.
   - No other section of the guide changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
c=$(awk '/^## The machine$/{on=1; next} /^## /{on=0} on' docs/operator-guide.md); printf '%s\n' "$c" | grep -c -F 'the login file for your runtime'; printf '%s\n' "$c" | grep -c -F 'means no key: podman'
```
Expect: two lines: `0`, `0`

```bash
awk '/^#### The two passes$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -F 'anthropic-api-key'
awk '/^### The stage image$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -F 'tests/test_stage_image.py tests/test_image.py'
```
Expect: two lines, each a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
