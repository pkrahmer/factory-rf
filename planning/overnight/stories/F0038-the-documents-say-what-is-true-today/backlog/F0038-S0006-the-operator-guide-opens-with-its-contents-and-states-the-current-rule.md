# The operator guide opens with its contents and states the current rule without its history

## Description

`docs/operator-guide.md` is for the operator (`CLAUDE.md`, *Docs*), and it has 1,468 lines and no contents list. Its first paragraph is the same build inventory as the README's (about 2,900 characters on one line, dated observations included) and ends with "The documenter stage extends this from each story's docs criterion", which is for agents. Across the guide, history stands where the operator needs the current rule: "Morning observations" with the planning ids WE3.1, WE3.3 and WE3.4, "treat it as the morning observation", "(R2)", "(decision 008 of factory-v2)", "(questionnaire 1, Q21)", "the five of before", "as before", "The token used to be a compose secret", and provenance notes such as "(seen at the tiny story of 2026-10-18 ...)", "(F0012-S0017)" and "(F0019-S0004 showed it)". The reasons behind these rules are in the decision log already. And the paragraph on the container's init (`init: true`, tini, catatonit, zombies after a killed run) stands under *The hosting-service token*, where an operator who sees `<defunct>` processes will not look. This story gives the guide an opening and a contents list, states each listed rule without its history, and gives the init a heading of its own (findings H3, M4 and M13 of the documentation review of 2026-10-20). The stop tables and the class names are F0038-S0007's and F0038-S0008's; the sections on mutation testing are F0032-S0001's.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, these changes and no other:
   - The paragraph under `# Operator guide` becomes exactly: "The guide for the person who runs the factory this repository implements: how to install and configure an instance, which stops it can reach and what to do about each. The machine's image is the usual way to run an instance (see "The machine's image")." It is followed by a list with one bullet per `##` section of the guide, in the guide's order, each bullet the section's exact title in double quotes and nothing else (`- "Install"`), as the guide cites sections. The inventory and the sentence on the documenter stage are gone.
   - *Install*: " (decision 008 of factory-v2)" is removed. *Configuration*: " (R2)" is removed.
   - "**Morning observations.**" becomes "**Checks on a running instance.**", and its table's cells lose the prefixes "WE3.1: ", "WE3.3: " and "WE3.4: ". "**Morning observation.**" (under *The hosting-service token*) becomes "**Checks on a running instance.**".
   - "Without it the words are the five of before." becomes "Without it the shell is started as `/bin/sh -c <script> factory-login <token file> claude ...`." (checked against `src/factory/adapters/agent_launch.py`: without an API login file the words are the shell, `-c`, the script, `factory-login` and the token file).
   - "The same status before the limit is a death, as before." becomes "The same status before the limit is a death." The sentence "An instance without the setting runs exactly as before." is removed. "is refused as before." becomes "is refused.". "A commit that also changes another file clears the stop as before." becomes "A commit that also changes another file clears the stop."
   - *Build it*: "The probe of 2026-10-17 built the image once under rootless Podman 5.8.3 in 42 s, without the pins (they were placeholders then). A build with the pins of `image/Dockerfile` is not observed yet; treat it as the morning observation." becomes "A build of the image with the pins of `image/Dockerfile` is not observed yet: check it once on a running instance."
   - *Claude Code*: "A maintenance feature after v1.1 updates the pin (questionnaire 1, Q21); until then it changes only when you edit the Dockerfile." becomes "The pin changes only when you edit the Dockerfile."
   - *The hosting-service token*: "The token used to be a compose secret with `uid`, `gid` and `mode`, but Compose ignores those three keys outside Swarm mode:" becomes "A compose secret cannot do it, because Compose ignores its `uid`, `gid` and `mode` outside Swarm mode:", and "A probe of 2026-10-17 read the token as the agent through that file." is removed.
   - The paragraph that begins "The service sets `init: true`" gets the heading `### The init` directly above it, inside *The container: compose, entrypoint and health check*; in it " (seen at the tiny story of 2026-10-18 under Docker Desktop)" is removed and "pile up as before" becomes "pile up".
   - *The health check and the restart policy*: "The probe of 2026-10-17 saw the health check run under Podman: it reported `starting`, then the text of the stop `repository_unavailable`, with exit 1. The morning observation that remains is `docker compose ps` over a container with a stop standing." becomes "Under Podman the health check reports `starting`, then the text of a stop in force, with exit 1. Not yet checked on a running instance: `docker compose ps` over a container with a stop in force."
   - *Container runtimes*: "(probe of 2026-10-17, Podman 5.8.3 on Windows)" becomes "(seen with Podman 5.8.3 on Windows)".
   - " (F0012-S0017)", " (seen by the coder of the tiny story, 2026-10-18)" and " (F0019-S0004 showed it)" are removed.
   - No heading of the guide is renamed or removed; `### The init` is the one heading added. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e 'orning observation' -e 'WE3.' -e 'decision 008' -e 'Q21' -e 'five of before' -e 'as before' -e 'used to be a compose secret' -e 'tiny story' -e 'F0012-S0017' -e 'F0019-S0004' -e 'probe of 2026-10-17' -e '(R2)' -e "documenter stage extends" docs/operator-guide.md || true
grep -c -x -F '### The init' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
uv run -q python - <<'EOF'
import re
from pathlib import Path

text = Path("docs/operator-guide.md").read_text(encoding="utf-8")
opening = text.split("\n## ", 1)[0]
titles = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
listed = re.findall(r'^- "(.+)"$', opening, flags=re.MULTILINE)
print(listed == titles, len(opening.split("\n\n")[1]) <= 400)
EOF
```
Expect: `True True` (the contents list names every `##` section in order, and the opening paragraph has at most 400 characters)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
