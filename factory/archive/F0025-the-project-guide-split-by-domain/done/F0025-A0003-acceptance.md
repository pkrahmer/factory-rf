---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 293
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T22:21:37.945197Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T22:25:51.960776Z'
  stage: acceptance
  run: c166a41d668c4d13a161804d88794397
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T22:27:03.100350Z'
  stage: done
stories: [F0025-S0001, F0025-S0002, F0025-S0003, F0025-S0004]
outcome: accepted
---

# Acceptance of The project guide split by domain

## Recommendation

**Accepted.** The guide is still an index and eight domain files, each under 600 lines (the largest has 377). All 41 old sections were moved byte for byte. `CLAUDE.md` and every other document lead to files that hold what they name. The document check reads all twelve files. S0004 closed the three module gaps found by A0002 and the sentence in the decision log that repeated itself, and `make check` is green.

One finding is left, and it is small:
- Since S0002, two stories of other features have written a module into a domain file without adding it to the index: `factory.application.project_agents` (F0022-S0001) and `factory.application.provider_limits` (F0020-S0007).
- One docs-only story is proposed for this (S0005).
- This is the second acceptance in a row to find this kind of drift, so whether the index should be kept complete by something lasting is listed for the human under 6.

## 1 Scope

The four archived stories, against `feature.md`:

- **S0001** built every scope bullet: `PROJECT_GUIDE`, `PROJECT_GUIDE_FOLDER` and `is_guide_file` in `src/factory/domain/documents.py`, the loop over the folder in `src/factory/entry/check_documents.py`, the move, and the references in `README.md`, `docs/operator-guide.md` and `docs/decisions.md`.
- **S0002** completed the index: the modules and the `### ` subsections other files point to.
- **S0003** pinned the line-edge behaviour of the wording check, and the usage line.
- **S0004** (A0002's proposal) was documents only:
  - it added `factory.adapters.preflight_stamp_file`, `factory.application.dispatcher` and `factory.domain.tick_status` to the `watching.md` line of the index;
  - it reworded the last sentence of *The project guide lives in `docs/`* in `docs/decisions.md`.

  Its diff touches only those two lines. Its tester, coder and reviewer each confirm that nothing under `src/` or `tests/` changed.

No story went outside the scope. The out-of-scope items still hold:
- the template and the demo keep one guide;
- the operator guide and the decision log are single files;
- the code tree did not move;
- there is no lasting layout or length test;
- the documenter's lesson is untouched;
- no paid call was made.

The human's changes:
- **Change 1** is on `main`.
- **Change 2:** no work item outside `done/` names `docs/project-guide.md`. The only lines that do are in `factory/features/F0019-…/feature.md` (fully archived), `F0025`'s own `feature.md` and the dated entries of `docs/decisions.md`, all of which are history.
- **Change 3:** `wc -l docs/project-guide/*.md` gives README 144, agents 325, costs 89, git-and-hosting 199, processes-and-checks 208, stages 307, watching 276, work-items 377 and write-guard 184. No file is near 600.

The goal is reached. The one shortfall is in the index, below.

## 2 Feature smoke test

What a user of the feature does, end to end:
1. An agent follows `CLAUDE.md` to the index.
2. From the index it finds the file for its module or section.
3. It finds the moved text unchanged.
4. The docs stage's check reads the whole guide and finds a v1 word anywhere in it.

The script is A0002's. I changed it in two ways: each part now reports its own problems (A0002's script carried one list through parts 3 to 5), and part 10 now checks S0004's two changes. The move is compared between the guide before the split (`61077acb:docs/project-guide.md`) and the folder at the end of S0001's docs stage (`10b669bf`).

Command, from the root of the checkout: `uv run -q python -I "$TMPDIR/feature_smoke.py"; echo "exit $?"`. The script:

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
found = {"3": problems}; problems = []
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
found["4"] = problems; problems = []
for doc in ("README.md", "docs/operator-guide.md", "CLAUDE.md"):
    t = Path(doc).read_text(encoding="utf-8")
    for f in re.findall(r"`(docs/project-guide[^`]*)`", t):
        problems += [f"{doc} names {f}, which is gone"] if not Path(f).exists() else []
    for f, sec in re.findall(r"`(docs/project-guide/[a-z-]+\.md)`, [\"*]([^\"*]+)[\"*]", t):
        if sec not in heads(Path(f).read_text(), 2) | heads(Path(f).read_text(), 3):
            problems.append(f"{doc}: {f} has no heading {sec!r}")
print("5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name:", not problems)
found["5"] = problems; problems = []
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
print("problems by part:", found)
# 10. S0004: the three modules described by class are on watching.md's index line, and the decision log no longer repeats itself.
wanted = ("factory.adapters.preflight_stamp_file", "factory.application.dispatcher", "factory.domain.tick_status")
print("10. watching.md's line names the three modules:", all(f"`{m}`" in listed["watching.md"] for m in wanted))
dec = Path("docs/decisions.md").read_text(encoding="utf-8")
print("    decision log: 'is an index and one file per domain' x", dec.count("Since F0025-S0001 the guide is an index and one file per domain"), "| 'is the folder' x", dec.count("Since F0025-S0001 the guide is the folder"))
```

Output:

```
1. CLAUDE.md names the index: True | names the old file: False | story form names the folder: True | old file exists: False
2. files and lines: {'README.md': 144, 'agents.md': 325, 'costs.md': 89, 'git-and-hosting.md': 199, 'processes-and-checks.md': 208, 'stages.md': 307, 'watching.md': 276, 'work-items.md': 377, 'write-guard.md': 184} | index lists every file: True | none over 600: True
3. the index lists each file's ## sections, in order: False
4. 41 old sections, each in one file and byte for byte unchanged at the move (but the named exceptions): True
   ## sections changed since the move: ['README.md: The files', 'agents.md: The agent definition reader', 'agents.md: The agent runtime', 'agents.md: The shipped agents, settings and template', 'git-and-hosting.md: The git wrapper', 'processes-and-checks.md: Mutation testing', 'processes-and-checks.md: Project commands', 'processes-and-checks.md: Starting a process', 'processes-and-checks.md: The duplicates report', 'stages.md: Stalls', 'stages.md: Starting a stage', 'stages.md: The claim service', 'stages.md: The pipeline definition', 'stages.md: The stage protocol', 'watching.md: Stops, the clock and the factory log', 'watching.md: The evaluation', 'watching.md: The tick', 'work-items.md: Identity, order and places of work items', 'work-items.md: The data of a work item', 'write-guard.md: The write paths']
5. README.md, the operator guide and CLAUDE.md name guide files that hold what they name: True
6. modules a domain file names: 122; on no index line of a file that names them: ['factory.application.project_agents', 'factory.application.provider_limits']
   modules under src/factory the guide names nowhere: 9: ['factory', 'factory.adapters', 'factory.application', 'factory.domain', 'factory.domain.fault_paths', 'factory.domain.kill_point_cases', 'factory.domain.kill_points', 'factory.entry', 'factory.entry.health']
7. cross-file references to a ### the index does not name: []
8. the document check reads 12 files; findings: []
9. a v1 word at an edge in costs.md: 'x\n\nEach ticket\nmoves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe run\nticket moves.\n' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticket' ["uses the v1 word 'ticket'"]
9. a v1 word at an edge in costs.md: 'x\n\nThe last ticketed' []
problems by part: {'3': ["processes-and-checks.md: the index lists ['Project commands', 'Starting a process', 'The duplicates report', 'The document check', 'The demos', 'Mutation testing', 'The report of a mutation run'], the file has ['Project commands', 'Starting a process', 'The duplicates report', 'The document check', 'The demos', 'Mutation testing']"], '4': [], '5': []}
10. watching.md's line names the three modules: True
    decision log: 'is an index and one file per domain' x 1 | 'is the folder' x 0
exit 0
```

The feature smoke test is **green** in what it promises: the move, the references, the file sizes and the document check. Where a line is not a plain `True`:

- **Part 3: `False`, but not a defect.** The index lists *Mutation testing* "(with *The report of a mutation run*)". That is a `### ` subsection F0024-S0001 added to `processes-and-checks.md`, and the script reads every starred name after `Sections:` as a `## ` section. The `## ` sections and their order match. The only problem is the form: the other lines name subsections after "Subsections other files refer to:". No file refers to this one, so I propose nothing.
- **Part 4, the sections changed since the move.** There are 20 now (5 at A0002). The new ones were written by F0020, F0022, F0023 and F0024 stories, each into the domain file of its code, which is what the split was for. No section moved to another file, and no `## ` heading the index lacks was added.
- **Part 6, the finding.** Two modules are named in a domain file but on no index line:
  - `factory.application.project_agents` is in `agents.md`, *The agent definition reader* (line 181, written by F0022-S0001 at `f3e654ba`);
  - `factory.application.provider_limits` is in `stages.md`, *Starting a stage* (line 199, written by F0020-S0007 at `6ae4b937`). The operator guide also names it, at line 233.

  An agent that searches the index for either module finds nothing. Proposed as S0005.
- **Part 6, the modules the guide names nowhere.** These are expected:
  - the five package roots;
  - `kill_points`, `kill_point_cases` and `fault_paths`, which the index names in its own sections.

  `factory.entry.health` is still described only in the operator guide. A0002 and S0004 both left it to a story that changes the module, and it stays there (section 5).
- **Part 10:** S0004's three modules are on the `watching.md` line, and the decision log no longer repeats itself.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0004** noticed nothing new:
  - the coder's entry 7 reads "Noticed, not touched: nothing";
  - the documenter's entry 11 reads "Stale text I saw but did not touch: none", and repeats that `factory.entry.health` is described only in the operator guide;
  - the reviewer (entry 9) had no remarks beyond the criteria.
- **`make duplicates`: 5 new, 33 known, 3 gone** (S0004 entry 7, and again today). Four of the new findings are similar-code findings between `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime`. The fifth is `unused class 'ManualWaiter'` in `src/factory/adapters/clock.py`. All are F0020's code, so they are for F0020's acceptance, as A0001 and A0002 said. None of them is F0025's.
- **From A0002's items:**
  - the three module gaps and the repeated sentence in the decision log are closed by S0004;
  - the stale `mutants/` copy was the human's;
  - mutation testing is now by sweep only (F0031).
- **My own observation:** the index drifts. Stories of other features write new modules into domain files, but their docs criteria do not name the index line. F0020-S0007 and F0022-S0001 each did this once. See S0005 and decision B under 6.

## 5 The documentation as a whole

I read, from the top:
- `README.md`'s pointers to the guide;
- the index;
- the openings of each domain file and the sections that changed since A0002;
- the operator guide's references to guide files;
- the decision log's two F0025 entries.

I found no contradiction between documentation and behaviour:
- every guide file that `README.md`, the operator guide and `CLAUDE.md` name holds the heading they name (part 5);
- *The document check* describes the command as it is built;
- the decision log's entry *The project guide lives in `docs/`* now reads once.

Smaller points:
1. **The index does not name `factory.application.project_agents` and `factory.application.provider_limits`** (section 2). Proposed as S0005.
2. **The index names a subsection in two ways.** On the `processes-and-checks.md` line it writes *Mutation testing* "(with *The report of a mutation run*)", and on the other lines "Subsections other files refer to: …". These are two forms, but they do not contradict each other. No story proposed.
3. **`factory.entry.health`** is described only in the operator guide. Describing it in the project guide would be new content, outside F0025's move-only scope. This is unchanged since A0002.

## 6 Decisions taken for the human

From `feature.md`, decisions 1 to 12, as A0002 listed them, to accept or revisit:
- one story;
- the index and eight domain files;
- about 600 lines a file, with no lasting length or layout test;
- a byte-for-byte move with two exceptions and no links;
- the move by script;
- the check reads the index as the guide and the folder's other files for words only;
- the template and the demo keep a single guide;
- the other documents follow in the same story;
- the leave for `tests/entry/test_check_documents.py`;
- independence from F0020 to F0024;
- testing in `tmp_path` plus the smoke test against `origin/main`;
- building F0025 before F0020-S0005.

From the stories:
- the decisions A0002 listed for S0001 to S0003:
  - S0001's `a.md.bak` row;
  - S0003's reviewer-added criterion 3;
  - S0002's documenter choosing the index line of a module that several files name, and its wording "It also names …";
- **S0004, coder entry 7:** both doc edits were left to the documenter, as the Interface says. This is no decision of weight.

Two points for the human to decide:
- **A. The two modules (S0005).** Should S0005 add `factory.application.project_agents` to the `agents.md` line and `factory.application.provider_limits` to the `stages.md` line, as S0002 did for the others? I would.
- **B. Keeping the index complete.** Decision 3 rejected a lasting layout test. Since then, two acceptances in a row have found modules missing from the index: three at A0002, all from the move, and two at A0003, from F0020-S0007 and F0022-S0001 after S0002. The options I see:
  1. keep things as they are, and each acceptance of F0025 or of the writing feature catches the gap;
  2. add one line to the documenter's lesson in `claude/agents/documenter.md`: a module newly named in a domain file goes on that file's index line (a coder write path; the feature put the lesson out of scope);
  3. make `make documents` check that every module a guide file names is on that file's index line, which revisits decision 3 and adds code.

  I would choose 2. It costs the least, and it acts in the story that adds the module. I did not propose it as a story, because the feature put the lesson out of scope, so this is the human's call.

Earlier tests changed:
- only `tests/entry/test_check_documents.py` in S0001, under decision 9;
- S0002 and S0004 changed no test (S0004's reviewer, entry 9: "no test file is changed, renamed or deleted");
- S0003 only added test modules.

No earlier test was changed without leave.

## 7 The slow checks

The project offers nothing beyond the make targets: `make check`, `make duplicates` (a record) and `make documents` (a check of the docs stage). There is no image scan and no SBOM. `make mutants` is a sweep and was not run (check 3).

- `make check` is **green** as I found it: `test: green (48.9 s)`, total coverage 99.12 %.
- The JUnit report (`.reports/junit.xml`) holds 6,005 tests, 455.8 s summed. The slowest are F0020's time-limit rows:
  - `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s;
  - `tests.adapters.test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s;
  - two rows of `tests.adapters.test_opencode_sudo_time_limit`: 4.5 s each;
  - `tests.adapters.test_claude_runtime_confinement::test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`: 3.1 s.
- F0025's own tests (the 208 rows whose names hold `documents`) take at most 0.13 s each.
- `make duplicates`: 5 new, 33 known, 3 gone, all F0020's (section 4).

**Disk:** the Disk now line and the Disk at the previous record line (both at acceptance) are identical: `/work` has 970.4 GB free and 0.5 GB used, and `/state` and `/tmp` are at 0.0 GB used. No growth. S0004 changed two lines of documents.

## 8 Cost

The four stories cost 32 runs, 22.2 min, 180 turns, 605,813 tokens in (2,900,632 more from cache), 60,490 out and $5.57:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 (the move, code and tests) | 10 | 9.7 | 2.74 |
| S0002 (the index) | 6 | 3.2 | 0.78 |
| S0003 (the line-edge tests) | 10 | 5.9 | 1.30 |
| S0004 (three modules, one sentence) | 6 | 3.4 | 0.76 |

- **S0001 still stands out:** about half the cost, which fits the only story with code, tests and the scripted move of 1,900 lines.
- **S0003** took one extra round for a criterion the reviewer added.
- **S0004** is documents-only, like S0002, and went through each stage once. Its tester and coder runs did nothing and say so, at about $0.25 together. That is the cost of a documents-only story going through the whole pipeline, and S0005 will cost about the same.

**Human interventions:** 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `backlog/F0025-S0005-the-guide-s-index-names-project-agents-and-provider-limits.md`: adds `factory.application.project_agents` to the `agents.md` line and `factory.application.provider_limits` to the `stages.md` line of the guide's index. Other features' stories wrote both modules into domain files after S0002 and left them off the index. Documents only, one small run.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed

   1. Scope: met.
      - S0001 to S0003 are as A0002 found them. S0004 closed A0002's three module gaps and the sentence in the decision log that repeated itself, by changing only two lines of documents.
      - Nothing was built outside the scope. The human's changes 1 to 3 hold, and no guide file is over 377 lines.
   2. Feature smoke test: green on the move, the references, the sizes and the document check.
      - All 41 sections moved byte for byte. The 20 sections changed since were each changed in the file of their domain.
      - The document check reads 12 files with no findings.
      - Finding: `factory.application.project_agents` (written by F0022-S0001) and `factory.application.provider_limits` (written by F0020-S0007) are named in domain files but on no line of the index. Proposed as S0005.
      - Part 3 shows `False` only because the index names *The report of a mutation run* in a different form; no defect.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: nothing new from S0004.
      - `make duplicates` reports 5 new, 33 known, 3 gone, all in F0020's runtimes and clock, so they are for F0020's acceptance.
      - The index drifts when other features' stories add modules to domain files.
   5. Documentation: no contradiction with behaviour. Two smaller points:
      - the two missing modules (S0005);
      - the index names subsections in two forms (no story proposed).

      `factory.entry.health` is still only in the operator guide, as before.
   6. Decisions: the feature's decisions 1 to 12 and the stories' choices stand. Two points for the human:
      - A: should S0005 add the two modules? I would.
      - B: how to keep the index complete. The options are: as now, a lesson line for the documenter, or a check in `make documents` (which revisits decision 3). I would choose the lesson line.

      No earlier test was changed without leave.
   7. Slow checks: nothing beyond the make targets.
      - `make check` is green: test 48.9 s, coverage 99.12 %, 6,005 tests.
      - The slowest tests are F0020's time-limit rows at 5.0 s. F0025's tests take at most 0.13 s.
      - Disk is unchanged from the previous record.
   8. Cost: 32 runs, 22.2 min, $5.57.
      - S0001 accounts for $2.74 (the move, code and tests).
      - S0004 cost $0.76, of which about $0.25 was tester and coder runs that did nothing.
      - 0 questions answered, 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 4.2 min, 27 turns, 67067 tokens in (1428595 more from cache), 16409 out, $1.15
