# The operator guide's opening after the first start

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014-S0013 brought `README.md`'s status paragraph up to the first start of 2026-10-17, and was told to make "no others" changes. Its documenter found the same stale sentence in the opening paragraph of `docs/operator-guide.md` (line 3) and left it, as the criterion said. That paragraph still ends its account of the container with: the image "was built and started once under rootless Podman (the probe of 2026-10-17, without the pins) up to the stop `repository_unavailable`; a run against a real repository with a token is not observed yet". At the first start of 2026-10-17, the instances `shakedown` (Docker Desktop) and `shakedown-podman` (rootless Podman) became healthy on the todo demo's empty project, the preflight's probe agent run included. A stage's agent run end to end, and a `time_limit` under `sudo`, are still to be observed at the shakedown run. An operator who reads the guide from the top now gets an older status than the README gives. This story aligns the guide's opening with the README.

This story is documentation only. The documenter writes it from the docs criterion.

## Interface

None. No code, image file or test changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in the opening paragraph of `docs/operator-guide.md`, the clause "a run against a real repository with a token is not observed yet" is replaced, in the README's words: the first start of 2026-10-17 brought two instances (Docker Desktop and rootless Podman) up healthy on an empty project, the preflight's probe agent run included, and a stage's agent run end to end and a `time_limit` under `sudo` are first observed at the shakedown run. The sentence on the Podman probe before it stays. Nothing else in the four documents changes; in particular, the "not observed yet" notes for the build with the pins and the Linux host's restart service stay, because the first start did not observe them.

## Demo

```bash
grep -c 'a run against a real repository with a token is not observed yet' docs/operator-guide.md; sed -n 3p docs/operator-guide.md | grep -c 'shakedown run'
```
Expect: two lines, `0` and then `1`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 acceptor: proposed by the feature acceptance of F0014.
