---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 257
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T09:32:13.881593Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T09:50:06.802420Z'
  stage: acceptance
  run: d495b122f4ec4778a9573fc90e9c3819
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T09:51:24.823693Z'
  stage: done
stories: [F0025-S0001, F0025-S0002, F0025-S0003]
outcome: accepted
---

# Acceptance of The project guide split by domain

## Recommendation

**Accepted.** The feature now does what `feature.md` promised. The guide is an index and eight domain files, and all 41 old sections moved byte for byte (apart from the two named exceptions). The index lists every file, every `## ` section and the four `### ` subsections other files point to, plus every module a file names by its dotted name. The document check reads all twelve files and finds a v1 word anywhere in a line. The "Done when" is met: the human's change 1 is on `main`, and `make check` is green. Both findings of the first acceptance (A0001) are closed by S0002 and S0003.

What is left is small:
- Three modules are described in `watching.md` only by their class names, so no index line names them. One small docs story is proposed for this (S0004).
- `make mutants` is red again, now because mutmut keeps a stale copy of the records-contract schemas in `mutants/`. That is the `Makefile`'s, which makes it the human's, and F0025 did not cause it.

## 1 Scope

The three archived stories, against `feature.md`:

- **S0001** built every scope bullet: `PROJECT_GUIDE` naming the index, `PROJECT_GUIDE_FOLDER` and `is_guide_file` in `src/factory/domain/documents.py:16-17,168`; the loop over the folder in `src/factory/entry/check_documents.py` (`_guide_files`); the move; and the references in `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. A0001 checked this in detail, and nothing has changed since.
- **S0002** (A0001's proposal) closed the scope gap A0001 found. The 62 modules missing from *The files* are now on their files' lines, and the index names *Boundaries* (the subsection decision 2 promised), *The records contract*, *The feature acceptance* and *The opencode runtime*. It changed documents only.
- **S0003** (A0001's proposal) added tests only. It pins the line-edge behaviour of the wording check and the usage line of `check-documents`.

No story went outside the scope. The template and the demo still have a single guide, the operator guide and the decision log are still single files, the code tree did not move, there is no lasting layout or length test, the documenter's lesson is untouched, and no story made a paid call.

The "Done when" is met:
- **Change 1** is on `main`: `CLAUDE.md` lines 3, 42 and 51 and `factory/story-form.md` line 15 name the index, the folder and `stages.md`, *The pipeline definition*.
- **Change 2** is done for the drafted stories still open. No work item outside `done/` in F0020 or F0021 names `docs/project-guide.md`; for example, F0020-S0006 criterion 15 names `docs/project-guide/agents.md`. Only `factory/features/F0019-the-write-guard-by-the-kernel/feature.md:22` still names the old path, and that feature is fully archived, so the line is history.
- **Change 3** has been observed. The first ordinary story after the split, F0020-S0005, had a documenter entry that changed `agents.md`, `stages.md` and `work-items.md` (the files the human's change 2 named) and cross-read the index (`F0020-S0005…md:858-870`).

## 2 Feature smoke test

What a user of the feature does, end to end:
1. An agent follows `CLAUDE.md` to the index.
2. From the index it finds the file for its module or section, including a `### ` subsection another file points to.
3. It finds the moved text unchanged.
4. The docs stage's check reads the whole guide and finds a v1 word in any file, at any place in a line.

The comparison is the guide before the split (`61077acb:docs/project-guide.md`) against the folder as S0001's docs stage left it (`10b669bf`). Sections that later stories changed are listed separately.

Command, from the root of the checkout: `d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run -q python -I "$d/feature_smoke.py"; echo "exit $?"`. The script:

```python
"""F0025 end to end: an agent goes from CLAUDE.md to the guide's index to its domain file; the docs stage checks every file."""
import re
import subprocess
from pathlib import Path

from factory.domain.documents import DOCUMENT_PATHS, check_documents, is_guide_file
from factory.domain.sections import sections, split_lines


def git_show(spec):
    return subprocess.run(["git", "show", spec], capture_output=True, encoding="utf-8", check=True).stdout


def parts(text):
    lines = split_lines(text)
    return {s.heading: "\n".join(lines[s.start : s.end]).rstrip() for s in sections(text)}


def heads(text, level):
    return {l[level + 1 :].strip() for l in text.splitlines() if l.startswith("#" * level + " ")}


problems = []
# 1. The first instruction an agent reads leads to the index, and the index exists.
claude = Path("CLAUDE.md").read_text(encoding="utf-8")
form = Path("factory/story-form.md").read_text(encoding="utf-8")
print("1. CLAUDE.md names the index:", "`docs/project-guide/README.md` is the guide for agents" in claude,
      "| names the old file:", "docs/project-guide.md" in claude, "| story form names the folder:", "docs/project-guide/" in form,
      "| old file exists:", Path("docs/project-guide.md").exists())
files = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("docs/project-guide").glob("*.md"))}
index = files["README.md"]
the_files = parts(index)["The files"]
listed = {m.group(1): line for line in the_files.splitlines() if (m := re.match(r"- `([^` ]+)`", line))}
print("2. files and lines:", {n: len(split_lines(t)) for n, t in files.items()}, "| index lists every file:", set(listed) == set(files),
      "| none over 600:", max(len(split_lines(t)) for t in files.values()) <= 600)
for name, text in files.items():
    named = re.findall(r"\*([^*]+)\*", listed.get(name, "").split("Sections:")[-1].split("Subsections other files refer to:")[0])
    if named != list(parts(text)):
        problems.append(f"{name}: the index lists {named}, the file has {list(parts(text))}")
print("3. the index lists each file's ## sections, in order:", not problems)
# 4. The move, against the guide before the merge and the folder at the end of S0001's docs stage.
old = parts(git_show("61077acb:docs/project-guide.md").replace("`docs/project-guide.md`", "`docs/project-guide/`"))
moved = {}
for n in files:
    moved[n] = git_show(f"10b669bf:docs/project-guide/{n}")
moved_parts = {n: parts(t) for n, t in moved.items()}
for h, text in old.items():
    holders = [n for n, p in moved_parts.items() if h in p]
    if len(holders) != 1 or (h != "The document check" and moved_parts[holders[0]][h] != text):
        problems.append(f"moved wrongly: {h} {holders}")
print(f"4. {len(old)} old sections, each in one file and byte for byte unchanged at the move (but the named exceptions):", not problems)
changed_since = sorted(f"{n}: {h}" for n, t in files.items() for h, body in parts(t).items() if moved_parts[n].get(h) != body)
print("   ## sections changed since the move:", changed_since)
for doc in ("README.md", "docs/operator-guide.md", "CLAUDE.md"):
    t = Path(doc).read_text(encoding="utf-8")
    for f in re.findall(r"`(docs/project-guide[^`]*)`", t):
        problems += [f"{doc} names {f}, which is gone"] if not Path(f).exists() else []
    for f, sec in re.findall(r"`(docs/project-guide/[a-z-]+\.md)`, [\"*]([^\"*]+)[\"*]", t):
        if sec not in heads(Path(f).read_text(), 2) | heads(Path(f).read_text(), 3):
            problems.append(f"{doc}: {f} has no heading {sec!r}")
print("5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name:", not problems)
# 6. From a module to its file: every module a domain file names is on that file's index line.
mods = {str(p.relative_to("src"))[:-3].replace("/", ".").removesuffix(".__init__") for p in Path("src/factory").rglob("*.py")}
named_by = {}
for n, t in files.items():
    if n == "README.md":
        continue
    for m in set(re.findall(r"factory\.(?:domain|application|adapters|entry)(?:\.[a-z_]+)+", t)):
        while m not in mods and m.count(".") > 2:
            m = m.rsplit(".", 1)[0]
        if m in mods:
            named_by.setdefault(m, set()).add(n)
gap = sorted(m for m, ns in named_by.items() if not any(f"`{m}`" in listed.get(n, "") for n in ns))
unguided = sorted(m for m in mods if not any(f"`{m}`" in line for line in listed.values()) and m not in named_by)
print(f"6. modules a domain file names: {len(named_by)}; on no index line of a file that names them: {gap}")
print(f"   modules under src/factory the guide names nowhere: {len(unguided)}: {unguided}")
# 7. Every '### ' heading another file refers to ("see *X*") is named in the index.
h2 = {n: heads(t, 2) for n, t in files.items()}
h3 = {n: heads(t, 3) for n, t in files.items()}
unresolved = []
for n, t in files.items():
    for ref in re.findall(r"see \*([^*]+)\*", t):
        home = [f for f in files if ref in h2[f] | h3[f]]
        if home and n not in home and not any(ref in h2[f] for f in home) and f"*{ref}*" not in the_files and "`" + home[0] + "`" not in t:
            unresolved.append(f"{n} -> {ref} ({home})")
print("7. cross-file references to a ### the index does not name:", unresolved)
# 8. The docs stage's check reads the whole guide.
texts = {p: Path(p).read_text(encoding="utf-8") for p in DOCUMENT_PATHS} | {f"docs/project-guide/{n}": t for n, t in files.items()}
print("8. the document check reads", sum(p in DOCUMENT_PATHS or is_guide_file(p) for p in texts), "files; findings:", check_documents(texts))
for edge in ("x\n\nEach ticket\nmoves.\n", "x\n\nThe run\nticket moves.\n", "x\n\nThe last ticket", "x\n\nThe last ticketed"):
    print("9. a v1 word at an edge in costs.md:", repr(edge), [f.message for f in check_documents(texts | {"docs/project-guide/costs.md": edge}) if "costs" in f.document])
print("problems:", problems)
```

Output:

```
1. CLAUDE.md names the index: True | names the old file: False | story form names the folder: True | old file exists: False
2. files and lines: {'README.md': 144, 'agents.md': 307, 'costs.md': 89, 'git-and-hosting.md': 197, 'processes-and-checks.md': 147, 'stages.md': 300, 'watching.md': 276, 'work-items.md': 375, 'write-guard.md': 184} | index lists every file: True | none over 600: True
3. the index lists each file's ## sections, in order: True
4. 41 old sections, each in one file and byte for byte unchanged at the move (but the named exceptions): True
   ## sections changed since the move: ['README.md: The files', 'agents.md: The agent runtime', 'agents.md: The shipped agents, settings and template', 'stages.md: Stalls', 'work-items.md: The data of a work item']
5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name: True
6. modules a domain file names: 115; on no index line of a file that names them: []
   modules under src/factory the guide names nowhere: 12: ['factory', 'factory.adapters', 'factory.adapters.preflight_stamp_file', 'factory.application', 'factory.application.dispatcher', 'factory.domain', 'factory.domain.fault_paths', 'factory.domain.kill_point_cases', 'factory.domain.kill_points', 'factory.domain.tick_status', 'factory.entry', 'factory.entry.health']
7. cross-file references to a ### the index does not name: []
8. the document check reads 12 files; findings: []
9. a v1 word at an edge in costs.md: 'x\n\nEach ticket\nmoves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe run\nticket moves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticket' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticketed' []
problems: []
exit 0
```

The feature smoke test is **green**. How to read the lines that are not plain `True`:

- **The changed sections (part 4).** They were all changed by later stories, which is what the move was for. S0002 changed *The files*. F0020-S0005 (`c3a71f43`) changed the other four, writing each change into the domain file of its code.
- **The modules the guide names nowhere (part 6).** Most of the list is expected:
  - the five package roots;
  - `kill_points`, `kill_point_cases` and `fault_paths`, which the index itself names in *Kill points* and *Fault-injection paths* (the script leaves out the index's own text).

  Four modules are real gaps:
  - `factory.application.dispatcher`, `factory.domain.tick_status` and `factory.adapters.preflight_stamp_file` are described in `watching.md` lines 84 to 94 and 250, but only by their class names (`Dispatcher`, `TickStatus`, `JsonPreflightStampFile`). So no index line leads to them. This is proposed as S0004.
  - `factory.entry.health` (`factory-health`) is described only in the operator guide. Describing it in the project guide would be new content, not part of the move (section 5).

## 3 Mutation score

`make mutants` is **red** before it scores anything:

```
$ make mutants
...
  File "/work/checkout/mutants/tests/domain/test_contract_login.py", line 33, in test_the_committed_cost_record_schema_lists_the_optional_login
    assert "login" in properties
AssertionError: assert 'login' in {'run': {'pattern': '^[0-9a-f]{32}$', 'title': 'Run', 'type': 'string'}, ...}
=========================== short test summary info ============================
FAILED tests/domain/test_contract_login.py::test_the_committed_cost_record_schema_lists_the_optional_login
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
failed to collect stats. runner returned 1
make: *** [Makefile:103: mutants] Error 1
```

**The cause is not F0025, and it is not the test.** mutmut 3.8.0 copies the files under `source_paths` into `mutants/` only when the target does not exist yet (`copy_src_dir` in `mutmut/utils/file_utils.py`: `if target_path.exists(): continue`). It refreshes the `.py` files by their modification time, but not the other files.

- The `mutants/` folder of this checkout is kept between runs, as the `Makefile` intends.
- It still holds `mutants/src/factory/contract/cost-record.schema.json` from 2026-10-19 00:13. That copy has no `login`.
- F0020-S0005 (`a4a6bd17`, 07:46) regenerated `src/factory/contract/cost-record.schema.json` with `login`, and its new test reads the schema from the copy.

So every `make mutants` on this checkout is red until the stale copy is gone. A0001's cause, the `test_process_streaming` deselect, is fixed on `main` (`0111e249`). Two possible fixes, both outside every write path (`Makefile`, or the operator's `mutants/` folder), so both are the human's:
- remove `mutants/src` before each run (the `.py` mutants are regenerated anyway), or
- add the contract folder to `also_copy` in `pyproject.toml`, which is copied every run.

For a score, I copied the checkout without `mutants/`, `.venv` and `.git` into a `mktemp -d` folder and ran the same mutmut call that `make mutants` builds for F0025:

```
$ TMPDIR="$d/t" UV_PROJECT_ENVIRONMENT=/work/checkout/.venv timeout 540 uv run --no-sync mutmut run "factory.domain.documents.*" "factory.entry.check_documents.*"
...
🎉 factory.entry.check_documents.x_main__mutmut_9
status 0 in 410 s
$ uv run --no-sync mutmut results --all true | grep -E "documents\.|check_documents\." | awk -F': ' '{print $NF}' | sort | uniq -c
    161 killed
      2 survived
```

The result is **161/163 killed** (98.8 %), up from 159/163 at A0001. S0003's tests kill the line-edge mutant (`x__without_replaced_section__mutmut_12`) and the program-name mutant (`x_main__mutmut_2`). The two survivors are the ones A0001 already judged equivalent, and they get no story:

- `factory.entry.check_documents.x__read__mutmut_2`: `encoding="utf-8"` → `encoding=None`. Python 3.12 coerces the C locale to UTF-8, so the default encoding in the container is UTF-8.
- `factory.entry.check_documents.x__read__mutmut_4`: `"utf-8"` → `"UTF-8"`, the same codec.

## 4 What the stories noticed

- **S0002's Description says "Three smaller passages" above a list of two.** This was noted by intake (entry 3), the coder (7), the reviewer (9), the documenter (11) and the smoke tester (13). The criteria named the right two passages, and the story is archived. Nothing to do.
- **`make duplicates`: 5 new, 35 known, 1 gone.** These are noted in S0002 and S0003 entries 7 and 15, and are still the same today: three similar-code findings between `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime`, plus `unused class 'OpencodeRuntime'` and `unused variable 'status_code'` in `opencode_runtime.py`. They are F0020's code, and F0020 still has stories open, so they belong to F0020's acceptance, as A0001 said.
- **S0003, coder entries 7 and 15:** the two equivalent encoding survivors are left as the story intended (section 3).
- **A0001's open items:**
  - change 1 is now on `main` (section 1);
  - the `see *The story form check*` reference now names `stages.md`;
  - the decision-log sentence was reworded by S0002, but it now repeats itself (section 5; folded into S0004).
- **My own observation:** `make mutants` keeps stale non-Python files in `mutants/src` (section 3). This is the human's.

## 5 The documentation as a whole

I read `README.md`, the index from the top, each domain file's opening, the operator guide's five references to guide files, *The document check* and the decision log's two F0025 entries. I found no contradiction between documentation and behaviour:

- `README.md:19` names the index.
- Every operator-guide reference names a file that holds the heading it names (smoke test, part 5).
- *The document check* (`processes-and-checks.md`) describes the command as built: it reads the guide's other files for words only, no subfolder, and findings in path order.

Smaller points:

1. **Three modules are named in `watching.md` only by their classes,** so the index cannot lead to them: `factory.application.dispatcher`, `factory.domain.tick_status` and `factory.adapters.preflight_stamp_file`. Proposed as S0004.
2. **`docs/decisions.md:23`, *The project guide lives in `docs/`*, says the same thing twice.** It opens with "`docs/project-guide/` is the guide for agents (R17)" (S0002's change) and ends with "Since F0025-S0001 the guide is the folder `docs/project-guide/`". This is not a contradiction, but the last sentence no longer says anything new. Folded into S0004.
3. **`factory.entry.health` (`factory-health`) is in no file of the project guide.** It is in the operator guide (line 3 and *The container: compose, entrypoint and health check*). Describing it is new content, outside F0025's move-only scope (Out of scope, second bullet). This is for the human to place: S0004 names it as left to a story that changes the module.
4. **Two size limits, as A0001 noted.** `claude/agents/documenter.md:72` says "well under the 2,000 lines"; the index (`README.md:5`) says "about 600 lines". These are consistent, and the lesson is out of scope.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:

1. One story, not two.
2. The index and eight domain files, filled by the modules their sections describe. *Stops, the clock and the factory log* goes to `watching.md`, and *Replaced from v1* goes to `agents.md`.
3. About 600 lines a file, checked once by the smoke test. There is no lasting length or layout test.
4. A move, byte for byte, with two exceptions, and no Markdown links.
5. The documenter moves the text with a script.
6. The document check reads the index as the guide, and every other `.md` file directly in the folder for its words only. No subfolder is read, and there is no stub at the old path.
7. The template and the todo demo keep a single guide.
8. The other documents follow in the same story, and dated decision entries stay.
9. Leave to change `tests/entry/test_check_documents.py`.
10. F0025 is independent of F0020 to F0024.
11. Testing in `tmp_path`, plus the smoke test against `origin/main`.
12. Build F0025 before F0020-S0005.

From the stories:

- **S0001, reviewer entry 9:** the reviewer added the `docs/project-guide/a.md.bak` → `False` row to criterion 2. A0001 listed this already.
- **S0001, coder entry 7:** guide files go through the existing word-only branch of `_messages`.
- **S0002, documenter entry 11:** where a module is named by several files, the documenter chose its index line:
  - `factory.domain.errors` → `stages.md`;
  - `factory.application.files` → `work-items.md`;
  - `factory.entry.wiring` → `watching.md`;
  - `factory.application.preflight` → `processes-and-checks.md`.

  S0002's criterion gave the rule ("the file that describes it"); the documenter judged each case.
- **S0002 introduced the wording** "It also names …" and "Subsections other files refer to:" on the index lines. The criterion named the second wording; the documenter chose the first.
- **S0003, reviewer entry 9:** the reviewer added criterion 3 (a longer word at the end of the text is not found) without asking the human. It is the refused side of a rule the Interface states, so it falls under `CLAUDE.md`'s rule that every limit is tested on both sides.
- **S0003, coder entries 7 and 15:** the `"\n"` join of the wording check is kept, and a line-by-line rework is rejected.

Earlier tests changed: only `tests/entry/test_check_documents.py` in S0001, under the feature's decision 9, which both of S0001's reviewer entries name. S0002 changed no test. S0003 only added `tests/domain/test_documents_line_edges.py` and `tests/entry/test_check_documents_usage.py`, and both of its reviewer entries say "Earlier tests: none" (status `A` only). No earlier test was changed without leave.

## 7 The slow checks

The project offers nothing beyond `make check`, `make mutants`, `make duplicates` (a record) and `make documents` (a check of the docs stage). There is no image scan and no SBOM.

- `make check` is **green**: `test: green (37.9 s)`, total coverage 99.05 %.
- **The JUnit report (`.reports/junit.xml`)** holds 5,519 tests, 427.6 s summed. The slowest are F0020's runtime time-limit rows and one fault path:
  - `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s;
  - `tests.test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]`: 3.4 s;
  - three rows of `test_claude_runtime_confinement` and `test_opencode_runtime_launch`: 3.0 s each.
- **F0025's own tests:** the 208 test rows whose names hold `documents` take at most 0.16 s each.
- **The mutation run** in the copy took 410 s. `make mutants` itself is red (section 3).
- `make duplicates`: 5 new, 35 known, 1 gone, all in F0020's runtimes (section 4).

**Disk:** at the acceptance, `/work` has 985.9 GB free and 0.5 GB used. At the previous record (the start) it was the same, and `/state` and `/tmp` are at 0.0 GB used at both. No growth. The mutation copy lives in this run's `$TMPDIR`, which the factory removes.

## 8 Cost

The stories cost 26 runs, 18.9 min, 151 turns, 515,799 tokens in (2,490,158 more from cache), 53,967 out and $4.81:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 (the move) | 10 | 9.7 | 2.74 |
| S0002 (the index) | 6 | 3.2 | 0.78 |
| S0003 (the line-edge tests) | 10 | 5.9 | 1.30 |

- **S0001 stands out.** It is more than half the cost, which fits: it is the only story with code, tests and the scripted move of 1,900 lines. A0001 found that the move itself took 80 s and $0.34. S0001's one extra round (about $0.72) came from the reviewer's test-only finding.
- **S0003 ran 10 runs for a test-only story.** The reviewer's criterion 3 sent it through doing → tests → doing → review again (entries 9 to 17), for one parametrize row.
- **S0002 is the cheapest shape.** A documents-only story went through each stage once.

**Human interventions:** 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `backlog/F0025-S0004-the-guide-s-index-names-the-modules-its-files-describe-by-class.md`: puts the three modules that `watching.md` describes only by their classes (`factory.application.dispatcher`, `factory.domain.tick_status`, `factory.adapters.preflight_stamp_file`) on the index line of `watching.md`. It also rewords the last sentence of the decision-log entry *The project guide lives in `docs/`*, which now repeats its first. Documents only, one small run.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed; make mutants red (a stale copy of the records-contract schemas is kept in `mutants/`), 161/163 killed in a clean copy

   1. Scope: met.
      - S0001 built every scope bullet.
      - S0002 closed A0001's index gap: 0 of 115 named modules missing, and the four `###` subsections are named.
      - S0003 pinned A0001's two real survivors.
      - Nothing was built outside the scope.
      - The human's change 1 is on `main`, change 2 is done for the drafted stories still open, and change 3 was seen in F0020-S0005's documenter entry.
   2. Feature smoke test: green.
      - `CLAUDE.md` leads to the index, the index lists all 9 files and their `##` sections in order, and no file is over 600 lines (the largest is 375).
      - All 41 sections moved byte for byte at `10b669bf`. The 5 sections changed since were changed by S0002 and F0020-S0005, in the right files.
      - The references in `README.md`, the operator guide and `CLAUDE.md` resolve.
      - The document check reads 12 files and finds a v1 word at the start or end of a line and at the end of the text.
      - Three modules are described only by their class names, so the index cannot lead to them (S0004).
   3. Mutation score: `make mutants` is red.
      - mutmut 3.8.0 copies a non-`.py` file under `src/` into `mutants/` only once, so `mutants/src/factory/contract/cost-record.schema.json` predates F0020-S0005's `login`, and `tests/domain/test_contract_login.py` fails the stats run.
      - The fix is the human's: clear `mutants/src` in the `Makefile`, or add the contract to `also_copy`.
      - In a clean copy: 161/163 killed. The 2 survivors are the equivalent encoding mutants.
   4. Noticed: S0002's "Three passages" slip (archived, nothing to do). The 5 new duplicates are F0020's. A0001's items are closed except the decision-log sentence, which now repeats itself (S0004).
   5. Documentation: no contradiction with behaviour.
      - Dispatcher, TickStatus and the preflight stamp file are named only by class (S0004), and the decision-log sentence repeats itself (S0004).
      - `factory-health` appears only in the operator guide; that is new content, for the human to place.
   6. Decisions: the feature's decisions 1 to 12 stand.
      - Reviewer additions: S0001's `a.md.bak` row and S0003's criterion 3 (the refused side of an Interface rule).
      - S0002's documenter chose the index line for each module that several files name.
      - The only earlier test changed is `tests/entry/test_check_documents.py`, under decision 9. Nothing was changed without leave.
   7. Slow checks: none beyond the make targets.
      - `make check` is green, with tests at 37.9 s and 99.05 % coverage.
      - The slowest tests are F0020's runtime time-limit rows (5.0 s and 3.x s); F0025's tests take at most 0.16 s.
      - The mutation run took 410 s. Disk use is unchanged since the start.
   8. Cost: 26 runs, 18.9 min, $4.81. S0001 accounts for $2.74 (the move, code and tests); S0003 took 10 runs for one reviewer-added row. 0 questions answered, 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 17.8 min, 40 turns, 119079 tokens in (2908363 more from cache), 27658 out, $2.09
