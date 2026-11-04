# The Debian packages decision points to the entry that superseded it

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

`docs/decisions.md` has the entry *Debian's packages follow the base image's release* (2026-11-01, F0047-S0006). It still says that the stage image installs seven Debian packages, `nodejs` and `npm` among them, and that `tests/test_stage_image.py` allows exactly those seven names. Since F0049-S0001, `vm/Dockerfile` installs six: `xz-utils` replaces `nodejs` and `npm`. `STAGE_PACKAGES` in `tests/test_stage_image.py` lists those six. The later entry *The factory's tools live apart, under `/opt/factory`, with their own Node* says that it supersedes the old one for those two packages. The old entry does not point forward, although the log's convention is that it should: other superseded entries carry a line `- Superseded in part by "<entry>": <what changed>.` (*Every tool of the machine's image is pinned*, for example, carries one that points to this very entry). A newcomer who reads the log from the top meets the seven packages first, with nothing that sends them on. This story adds that one line to the old entry. It does not rewrite the entry's other lines, which stay as the record of what was decided on 2026-11-01. No code and no test change.

## Interface

- No module under `src/factory/` changes, and no test. The story changes `docs/decisions.md` only.
- The line the documenter adds as the last bullet of *Debian's packages follow the base image's release*, in the form the log already uses: `- Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node": the image installs six Debian packages, `xz-utils` in place of `nodejs` and `npm`, and `tests/test_stage_image.py` allows those six names.`

## Acceptance criteria

1. `docs/decisions.md`, the entry *Debian's packages follow the base image's release*: it ends with one bullet that starts `Superseded in part by "The factory's tools live apart, under `/opt/factory`, with their own Node"` and names the six packages and `xz-utils` in place of `nodejs` and `npm`. The entry's other bullets are unchanged, and no other entry of the log changes. Without the line, the entry has no forward pointer at all, which is the state this story ends.
2. `make check` stays green.
3. docs: `docs/decisions.md` as criterion 1 says. `README.md`, `docs/operator-guide.md` and the project guide: none, because they already name the six packages (`docs/operator-guide.md`, *The stage image*) or do not name them at all.

## Smoke test

```bash
grep -c 'Superseded in part by "The factory.s tools live apart' docs/decisions.md
sed -n '/^## Debian.s packages follow the base image.s release/,/^## /p' docs/decisions.md | grep -c 'xz-utils'
uv run python -m factory.entry.check_documents
```

Expect: `1`, then `1`, then `documents ok` (uv may print a `Bytecode compiled` line before it).

## Journal
