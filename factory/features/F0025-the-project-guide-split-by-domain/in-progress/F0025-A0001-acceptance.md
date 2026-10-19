---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 253
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T07:00:37.439795Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T07:22:37.407855Z'
  stage: acceptance
  run: 60522f5a2bfb44e39ad439875ea68eb3
stories: [F0025-S0001]
outcome: null
---

# Acceptance of The project guide split by domain

## Recommendation

Accepted with stories. The move is complete and exact. All 41 sections of the old guide are each in exactly one of the nine files, unchanged except for the two named exceptions. No file passes 600 lines (the largest is 375). The document check reads all twelve files, flags a v1 word in a domain file and ignores subfolders. `make check` is green. Two findings are worth stories, and neither breaks a promise:

- The index does not do all its job. In *The files*, 62 of the 114 modules that the domain files name appear on none of the lines that should point to them. The `### Boundaries` that feature decision 2 promised for the index is not there either.
- Mutation testing found that no test notices the document check missing a v1 word at the edge of a line.

The feature is not "done" by its own definition yet: the human's change 1 (`CLAUDE.md` and `factory/story-form.md`) is not on `main`. So every agent run, this one included, is still told to read `docs/project-guide.md`, which no longer exists. That change is the human's, not a story's.

## 1 Scope

The feature has one story, S0001, and it covers every scope bullet:

- **`factory.domain.documents`:** `PROJECT_GUIDE_FOLDER = "docs/project-guide"`, `PROJECT_GUIDE` built from it as `docs/project-guide/README.md`, `is_guide_file` (`rpartition("/")` plus `fullmatch` of `[^/]+\.md`, with the index left out), and `check_documents` over the sorted guide files after the four documents.
- **`factory.entry.check_documents`:** `_guide_files(root)` lists the regular files directly in the folder.
- **Tests:** `tests/domain/test_documents_guide_files.py` and `tests/entry/test_check_documents_guide_files.py`, plus the earlier module of decision 9.
- **The move:** the guide is now the nine files of decision 2. `docs/project-guide.md` is gone.
- **The other documents:** `README.md`, `docs/operator-guide.md` and `docs/decisions.md` were updated (`git diff 61077acb a148571d`).

No story went outside the scope:

- The template's and the demo's single guide are untouched.
- The operator guide and the decision log are still single files.
- The code tree did not move.
- There is no lasting layout or length test.
- The documenter's lesson is unchanged.
- No paid call was made.

There are two gaps against the Goal and the decisions:

1. **The index is incomplete.** S0001's criterion 8 says each line of *The files* names "the packages, modules and commands its sections describe". Of the 114 modules under `src/factory/` that the eight domain files name, 62 appear on no index line of a file that names them. Among them:
   - `factory.adapters.opencode_runtime`, `factory.application.preflight` and `factory.domain.settings`;
   - the feature acceptance's `factory.application.acceptance` and `factory.domain.acceptance`;
   - every module of `factory.application.handlers`;
   - `factory.application.scheduler` and `factory.entry.wiring`.

   An agent whose story touches one of these cannot get from the index to the file. Decision 2 also says "the index names *Boundaries* in its list", but S0001's criterion did not carry that over and the index does not name it. The same is true of the other `### ` subsections the human's change 2 sends later stories to: *The records contract* in `work-items.md` and *The opencode runtime* in `agents.md`.
2. **The "Done when" is not met.** It includes "the human's change 1 is on `main`", and it is not:
   - `CLAUDE.md` lines 3, 42 and 51 still name `docs/project-guide.md`;
   - `factory/story-form.md` line 15 still names it too.

   The human's change 2 (rewording the drafted stories' docs criteria) is also still open: F0020-S0005, F0020-S0006, F0020-S0007, `F0020/feature.md` and `F0019/feature.md` still name the old path. Neither change is a story's to make (they are protected paths, or work items that are not this acceptance's).

The fix for gap 1 is proposed as S0002.

## 2 Feature smoke test

The walk-through follows what the feature is for:

1. An agent opens the index and finds the file of its domain, together with that file's sections and modules.
2. The moved text is the old text.
3. The other documents point to guide files that hold what they name.
4. The docs stage's document check reads the whole guide and finds a fault in any of its files.

The comparison is against the guide as it was before the merge, `61077acb:docs/project-guide.md`.

Command, from the root of the checkout: `uv run -q python -I "$d/feature_smoke.py"`, where `$d` is a `mktemp -d` folder. The script:

```python
"""F0025 end to end: an agent goes from the guide's index to its domain file; the docs stage checks every file."""
import re
import subprocess
import sys
from pathlib import Path

from factory.domain.documents import DOCUMENT_PATHS, check_documents, is_guide_file
from factory.domain.sections import sections, split_lines


def parts(text):
    lines = split_lines(text)
    return {s.heading: "\n".join(lines[s.start : s.end]).rstrip() for s in sections(text)}


def heads(text, level):
    return {l[level + 1 :].strip() for l in text.splitlines() if l.startswith("#" * level + " ")}


problems = []
old = subprocess.run(["git", "show", "61077acb:docs/project-guide.md"], capture_output=True, encoding="utf-8", check=True).stdout
files = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("docs/project-guide").glob("*.md"))}
index = files["README.md"]
the_files = parts(index)["The files"]
listed = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
print("1. files and lines:", {n: len(split_lines(t)) for n, t in files.items()})
for name, text in files.items():
    named = re.findall(r"\*([^*]+)\*", listed.get(name, "").split("Sections:")[-1])
    if named != list(parts(text)):
        problems.append(f"{name}: the index lists {named}")
print("2. the index lists each file's ## sections, in order:", not problems)
oldparts = parts(old.replace("`docs/project-guide.md`", "`docs/project-guide/`"))
for h, text in oldparts.items():
    holders = [n for n, t in files.items() if h in parts(t)]
    if len(holders) != 1 or (h != "The document check" and parts(files[holders[0]])[h] != text):
        problems.append(f"moved wrongly: {h} {holders}")
print(f"3. {len(oldparts)} old sections, each in one file and unchanged but the named exceptions:", not problems)
for doc in ("README.md", "docs/operator-guide.md"):
    t = Path(doc).read_text(encoding="utf-8")
    for f in re.findall(r"`(docs/project-guide[^`]*)`", t):
        problems += [f"{doc} names {f}, which is gone"] if not Path(f).exists() else []
    for f, sec in re.findall(r"`(docs/project-guide/[a-z-]+\.md)`, \"([^\"]+)\"", t):
        problems += [f"{doc}: {f} has no heading {sec!r}"] if sec not in heads(Path(f).read_text(), 2) | heads(Path(f).read_text(), 3) else []
print("4. README.md and the operator guide name guide files that hold what they name:", not problems)
texts = {p: Path(p).read_text(encoding="utf-8") for p in DOCUMENT_PATHS} | {f"docs/project-guide/{n}": t for n, t in files.items()}
print("5. the document check reads", sum(p in DOCUMENT_PATHS or is_guide_file(p) for p in texts), "files; findings:", check_documents(texts))
mods = {str(p.relative_to("src"))[:-3].replace("/", ".").removesuffix(".__init__") for p in Path("src/factory").rglob("*.py")}
named_by = {}
for n, t in files.items():
    for m in set(re.findall(r"factory\.(?:domain|application|adapters|entry)(?:\.[a-z_]+)+", t)) if n != "README.md" else ():
        while m not in mods and m.count(".") > 2:
            m = m.rsplit(".", 1)[0]
        named_by.setdefault(m, set()).add(n) if m in mods else None
gap = sorted(m for m, ns in named_by.items() if not any(f"`{m}`" in listed.get(n, "") for n in ns))
print(f"6. modules a domain file names: {len(named_by)}; on no index line of a file that names them: {len(gap)}, e.g. {gap[:6]}")
h3 = {n: heads(t, 3) for n, t in files.items()}
for sub in ("Boundaries", "The records contract", "The opencode runtime", "The feature acceptance"):
    print(f"7. ### {sub}: in {[n for n in files if sub in h3[n]]}, named in the index: {f'*{sub}*' in the_files}")
print("problems:", problems)
```

Output (`exit 0`):

```
1. files and lines: {'README.md': 144, 'agents.md': 301, 'costs.md': 89, 'git-and-hosting.md': 197, 'processes-and-checks.md': 147, 'stages.md': 300, 'watching.md': 276, 'work-items.md': 375, 'write-guard.md': 184}
2. the index lists each file's ## sections, in order: True
3. 41 old sections, each in one file and unchanged but the named exceptions: True
4. README.md and the operator guide name guide files that hold what they name: True
5. the document check reads 12 files; findings: []
6. modules a domain file names: 114; on no index line of a file that names them: 62, e.g. ['factory.adapters.atomic_file', 'factory.adapters.claude_guard', 'factory.adapters.clock', 'factory.adapters.disk_space', 'factory.adapters.factory_log', 'factory.adapters.fake_agent_runtime']
7. ### Boundaries: in ['watching.md'], named in the index: False
7. ### The records contract: in ['work-items.md'], named in the index: False
7. ### The opencode runtime: in ['agents.md'], named in the index: False
7. ### The feature acceptance: in ['work-items.md'], named in the index: False
problems: []
```

Then I ran the document check as the docs stage runs it, on a copy of the four documents and the guide in `$d/r`. I added three faults:
- a v1 word and a replaced phrase in `watching.md`;
- a `## Replaced from v1` row in `costs.md`, which is allowed;
- `old/x.md` with a v1 word, in a subfolder.

After that I deleted the index:

```
$ uv run -q python -m factory.entry.check_documents --root "$d/r"; echo "exit $?"
docs/project-guide/watching.md: describes a replaced behaviour: 'run record'
docs/project-guide/watching.md: uses the v1 word 'ticket'
exit 1
$ rm "$d/r/docs/project-guide/README.md"; uv run -q python -m factory.entry.check_documents --root "$d/r"; echo "exit $?"
docs/project-guide/README.md: missing
docs/project-guide/watching.md: describes a replaced behaviour: 'run record'
docs/project-guide/watching.md: uses the v1 word 'ticket'
exit 1
$ uv run -q python -m factory.entry.check_documents; echo "exit $?"
documents ok
exit 0
```

The smoke test is green. Parts 1 to 5 hold the move, the references and the check. Parts 6 and 7 are the index finding of section 1. I also resolved every "see *X*" in the guide against the headings of all nine files:
- Two references are bold paragraph labels inside their own section (*Confinement* in `agents.md`, *Rewritten after every undo* in `costs.md`), as they were before the move.
- One reference points to a decision-log entry and says so.
- One reference crosses files without saying where. `agents.md`, *The shipped agents, settings and template*, has "see *The story form check*". That is a `###` in `stages.md`, and its name is close to `work-items.md`'s `## The form check of a story`. It is folded into S0002.

## 3 Mutation score

`make mutants` is **red** before it scores anything. The command and the end of its output:

```
$ make mutants
...
  File "/work/checkout/mutants/tests/adapters/test_process_streaming.py", line 321, in test_run_process_shares_the_one_popen_line_and_reports_no_stop
    assert len(popen_lines) == 1
AssertionError: assert 20 == 1
 +  where 20 = len(['    return subprocess.Popen(  # noqa: S603  # nosec B603', ...])
=========================== short test summary info ============================
FAILED tests/adapters/test_process_streaming.py::test_run_process_shares_the_one_popen_line_and_reports_no_stop
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
failed to collect stats. runner returned 1
make: *** [Makefile:103: mutants] Error 1
```

The cause is not F0025. `tests/adapters/test_process_streaming.py::test_run_process_shares_the_one_popen_line_and_reports_no_stop` came from F0020-S0003 (`3cc10c93`). It reads the source of `factory.adapters.process`, which mutmut rewrites with trampolines, so it fails in mutmut's stats run. It is not in the `--deselect` list of `[tool.mutmut]` in `pyproject.toml`, which names exactly such structural tests. Until it is added there, `make mutants` is red for every feature. The fix is one line in `pyproject.toml`, which is outside every write path, so it is the human's to make (or F0020's, through its *The human's changes*). It is not a story here.

For a score, I copied the checkout into a `mktemp -d` folder, added that one `--deselect` line to the copy's `pyproject.toml`, and ran the same mutmut call `make mutants` builds:

```
$ TMPDIR="$d/t" UV_PROJECT_ENVIRONMENT=/work/checkout/.venv timeout 540 uv run --no-sync mutmut run "factory.domain.documents.*" "factory.entry.check_documents.*"
status 0 in 376 s
163/14216  🎉 159 🫥 0  ⏰ 0  🤔 0  🙁 4  🔇 0
```

The result is **159/163 killed** (97.5 %). The four survivors, by module and rule (`mutmut show`):

- **`factory.domain.documents`, the wording check at a line's edge** (`x__without_replaced_section__mutmut_12`): `"\n".join(...)` became `"XX\nXX".join(...)`. This is a real gap. Under the mutant, every v1 word at the start or end of a line is glued to `XX`, fails the word-edge test of `_uses_word`, and is missed. Every test puts its v1 word mid-line (for example `Each ticket moves on.`). The missing criterion: a v1 word at the end of a line, at the start of a line and at the end of the text is found, and a longer word at the same edges is not. Proposed as S0003.
- **`factory.entry.check_documents`, the program name** (`x_main__mutmut_2`): `ArgumentParser(prog=_PROGRAM)` became `prog=None`. No test reads the usage line, which today reads `usage: check-documents [-h] [--root ROOT]`. The missing criterion: a bad argument exits with 2 and names `check-documents`. Folded into S0003.
- **`factory.entry.check_documents._read`, the encoding** (`mutmut_2`, `encoding=None`; `mutmut_4`, `"UTF-8"`): both are equivalent here. `"UTF-8"` is the same codec, and Python 3.12 coerces the C locale to UTF-8, so the default encoding is UTF-8 in the container. No story.

## 4 What the stories noticed

- **Coder, entries 7 and 15: `make documents` is red until the docs stage moves the guide.** Resolved: the docs stage ended with `documents ok`, and it is green on `main` now (section 2).
- **Coder, entries 7 and 15: `tests/test_claude_files.py` still quotes `CLAUDE.md`'s sentence.** Not quite: its line 97 pins `template/CLAUDE.md`'s sentence. Decision 7 keeps that sentence on purpose, and the human's change 1 does not touch it. Nothing to do.
- **Documenter, entry 19: the F0011-S0005 entry of `docs/decisions.md` names the old path.** It is dated history, and decision 8 keeps it. Nothing to do.
- **Documenter, entry 19: `CLAUDE.md`, `factory/story-form.md` and `tests/test_claude_files.py` name the old path.** `CLAUDE.md` and the story form are the human's change 1, still open (section 1). It is the most urgent open item, because every agent's first instruction names a file that is gone. `tests/test_claude_files.py` is as above.
- **Documenter, entry 19: the guide's "see *Section*" references name no file.** By design (decision 4), the index leads from a name to its file. That works for the 41 `## ` headings but not for `### ` headings. One reference crosses files to a `###`, and *Boundaries* is not named (section 1). Folded into S0002.
- **Reviewer, entries 9 and 17: 5 new `make duplicates` findings in `claude_runtime` and `opencode_runtime`.** They are still there today (`duplicates: 5 new, 35 known, 4 gone`), among them `unused class 'OpencodeRuntime'` and `unused variable 'status_code'`. They are F0020's code, which is still open (S0005 to S0008 are in its backlog). They belong to F0020's acceptance, not here.
- **My own observation:** `write-guard.md`, *The write paths*, says `PROTECTED_PATHS` has ten patterns. That is true today (10). F0022-S0001 will make it eleven, and the human's change 2 already names the file it goes to. Nothing to do.

## 5 The documentation as a whole

I read `README.md`, the index and the eight files' openings, the operator guide's five references, and the two decision entries. I found no contradiction between documentation and behaviour:
- Every reference in `README.md` and the operator guide names a file that exists and holds the section it names (section 2, part 4).
- *The document check* in `processes-and-checks.md` describes the code as built.
- Every domain file opens with its title and "read the index, `README.md`, first".

Smaller points:

1. **The index's module lists are incomplete, and `### ` subsections are not named.** See section 1; S0002.
2. **`docs/decisions.md`, *The project guide lives in `docs/`*, contradicts itself.** It still opens with "`docs/project-guide.md` is the guide for agents (R17)" and then adds "Since F0025-S0001 the guide is the folder `docs/project-guide/`". A newcomer reads a present-tense sentence about a file that is gone. This is not a dated entry, so it can be reworded. Folded into S0002.
3. **Two size limits.** The shipped documenter lesson (`claude/agents/documenter.md:72`) says each file stays "well under the 2,000 lines", while the index and the decision log say "about 600 lines". These are not contradictory (600 is well under 2,000), and the feature put the lesson out of scope. I note it only for the human's change 3.
4. **The template and the todo demo** keep `docs/project-guide.md` by decision 7. This is consistent.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:

1. One story, not two.
2. The index and eight domain files, filled by the modules their sections describe. *Stops, the clock and the factory log* goes to `watching.md`, and *Replaced from v1* goes to `agents.md`.
3. About 600 lines a file, checked once by the smoke test. There is no lasting length or layout test.
4. A move, byte for byte, with two exceptions (the path sentence of *The write paths* and *The document check*), and no Markdown links.
5. The documenter moves the text with a script.
6. The document check reads the index as the guide, and every other `.md` file directly in the folder for its words only. Subfolders are not read, and there is no stub at the old path.
7. The template and the todo demo keep a single guide.
8. The other documents follow in the same story, and dated decision entries stay as they are.
9. Leave to change `tests/entry/test_check_documents.py`.
10. F0025 is independent of F0020 to F0024.
11. Testing in `tmp_path`, plus the smoke test against `origin/main`.
12. Build F0025 before F0020-S0005.

From the stories:

- **Reviewer, entry 9:** the reviewer added a row to criterion 2 itself (`docs/project-guide/a.md.bak` gives `False`), to pin the refused side of "fully matches". It is a test of the Interface's own rule, but it was decided without the human.
- **Coder, entry 7:** guide files go through the existing word-only branch of `_messages`. A separate function was rejected.

Earlier tests changed: `tests/entry/test_check_documents.py`. Only its `MISSING_LINES` and one expected line of `test_each_finding_prints_one_line_in_order_and_returns_one` changed. The leave was the feature's decision 9, which both reviewer entries (9 and 17) name. No earlier test was changed without leave. The new `tests/entry/test_check_documents_guide_files.py` imports `MISSING_LINES` from that module. That is a shared constant read across test modules, not a change.

## 7 The slow checks

The project offers nothing beyond `make check`, `make mutants`, `make duplicates` (a record) and `make documents` (the docs stage's check, `documents ok`). There is no image scan and no SBOM.
- `make check` is green; `make test` took 36.6 s.
- The JUnit report holds 5,418 tests, 377.4 s summed. The slowest are F0020's runtime tests: `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` takes 5.0 s, and three `test_claude_runtime_confinement` and `test_opencode_runtime` time-limit rows take 3.0 s each.
- This feature's 25 new test rows each take 0.01 s or less.
- `make mutants` is red (section 3). The diagnostic run took 376 s.

Disk: `/work` 0.5 GB used at the acceptance, the same as at the previous record (start). `/state` and `/tmp` are at 0.0 GB at both. No growth.

## 8 Cost

The story cost 10 runs, 9.7 min, 73 turns, 286,960 tokens in (1,492,179 more from cache), 30,961 out and $2.74. Human interventions: 0 questions answered, 0.0 h waited.

There is only one story, so none stands out against another. Within it, the most expensive run was the first tester run ($0.46, 13 turns, 99 s). The documenter's move, which decision 1 sized for 40 minutes, took 80 s and $0.34. That is the scripted move of decision 5 paying off.

The one extra round (coder, tester, coder and reviewer again, about $0.72 together) came from the reviewer's single finding, the `a.md.bak` row. It needed no code. No story needed the human.

## Proposed stories

- `backlog/F0025-S0002-the-guide-s-index-names-every-module-and-subsection-its-files-describe.md`: completes the index's module lists (62 of 114 missing) and names the `### ` subsections other files and the human's change 2 point to (*Boundaries*, as decision 2 promised, *The records contract*, *The opencode runtime*, *The feature acceptance*). It also makes the one cross-file reference name its file, and rewords the decision entry that still calls `docs/project-guide.md` the guide. Documents only.
- `backlog/F0025-S0003-the-document-check-finds-a-v1-word-at-a-line-s-edge-and-names-itself-in-its-usage.md`: the two real survivors of the mutation run, pinned as criteria. A v1 word at the edge of a line or of the text is found, and a bad argument prints `check-documents`' usage and exits with 2. Tests only; the code already does both.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 2 stories proposed; make mutants red (a test from F0020-S0003 breaks mutmut's stats run), 159/163 in a copy with that test deselected

   1. Scope: S0001 covers every scope bullet; nothing outside scope was built. Two gaps:
      - The index's *The files* misses 62 of the 114 modules the domain files name. It also does not name `### Boundaries`, which decision 2 promised, or the other subsections that change 2 points stories to (S0002).
      - The feature's "Done when" is not met: the human's change 1 is not on `main`. `CLAUDE.md` lines 3, 42 and 51 and `factory/story-form.md` line 15 still name `docs/project-guide.md`, which no longer exists. Change 2 is also still open.
   2. Feature smoke test: green, run against `61077acb:docs/project-guide.md`.
      - All 41 sections are in exactly one file each, unchanged apart from the two named exceptions.
      - The index lists every file's `##` sections in order, and the README and operator-guide references resolve.
      - No file passes 600 lines; the largest is 375.
      - The document check reads all 12 files, flags a v1 word in a domain file, ignores a subfolder, and reports a missing index.
   3. Mutation score: `make mutants` is red. `tests/adapters/test_process_streaming.py::test_run_process_shares_the_one_popen_line_and_reports_no_stop` (from F0020-S0003) reads the source mutmut rewrites and is missing from the `[tool.mutmut]` deselect list in `pyproject.toml`. That one-line fix is the human's.
      - In a copy with that test deselected: 159/163 killed.
      - Real survivors: a v1 word at a line's edge is never tested, and neither is the program name in the usage line (S0003).
      - The two encoding survivors are equivalent.
   4. Noticed items:
      - The `make documents` gap was resolved by the docs stage.
      - The `test_claude_files` note concerns the template's sentence, which decision 7 keeps.
      - The dated decision entry stays as history.
      - Change 1 is open (above).
      - Subsection references are folded into S0002.
      - The 5 new duplicates findings are in F0020's runtimes and belong to F0020.
   5. Documentation: no contradiction with behaviour. Smaller points:
      - The index is incomplete (S0002).
      - The decision entry *The project guide lives in `docs/`* still opens by calling the gone file the guide (S0002).
      - The documenter lesson's 2,000-line limit sits beside the guide's 600-line limit; noted for the human only.
   6. Decisions taken for the human:
      - The feature's decisions 1 to 12.
      - The reviewer added the `a.md.bak` row to criterion 2 without asking the human.
      - `tests/entry/test_check_documents.py` was changed under decision 9, which both reviewer entries name. No unleaved change.
   7. Slow checks: nothing beyond `make check`, `make mutants`, `make duplicates` and `make documents`.
      - `make test` took 36.6 s. The slowest tests are F0020's runtime time-limit rows (5.0 s and 3.0 s).
      - Disk is unchanged since the start (/work 0.5 GB used).
   8. Cost: 10 runs, 9.7 min, $2.74; 0 human questions and 0.0 h waited.
      - The scripted move cost $0.34 in 80 s.
      - The one extra round (about $0.72) came from the reviewer's test-only finding.
