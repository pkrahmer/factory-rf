# The project guide names every passage of v1.1's own in the shipped agents

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`docs/project-guide/agents.md`, *The seven agents*, says the shipped bodies carry v1's texts, "the sentences are not rewritten in other words", and that "Six passages are v1.1's own text and not v1's". F0034-S0002 raised that count from three to six, and the renaming table under *Replaced from v1* repeats it as "except the six passages". The count is still short. `git log -- claude/agents/` after `830029c9` (F0010-S0017, which carried v1's texts in) shows at least four more passages of v1.1's own outside `## Lessons`. R14's write-guard sentences come from F0019-S0006: the kernel refuses every other write, a refused write fails with `Permission denied`, and temporary files go only in `$TMPDIR`. Rule R15 on a project's skills and agents comes from F0022-S0002. The `acceptance-reviewer`'s comparison of the Disk now line with the previous record, in its check 7, comes from F0012-S0017. Its check 3, *Mutation testing*, "By sweep, not run here", comes from F0031-S0001, together with the words that story changed in its check 7, its recommendation, its proposals paragraph and its stage steps 1 and 3. The guide already describes R14 (the `## Rules` bullet) and R15 (the paragraph on skills), but it does not count them as v1.1's own. It does not mention the acceptance reviewer's check 3 or its disk comparison at all. An agent that changes an agent text reads the guide to learn which sentences are v1's and must keep v1's words. With a closed count that goes stale at every new passage, the guide tells it wrongly. This story is for that agent. It makes the guide name every passage of v1.1's own, each with the story that wrote it, with no number that the next passage would make wrong. The agent texts, the tests, the operator guide, the decision log and the playbook stay as they are. It changes no behaviour, so it has no criterion beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks the list against `git log -p 830029c9.. -- claude/agents/`, and against the shipped bodies under `claude/agents/` as they are. Every sentence there that is not in v1's text and is not under `## Lessons` is one of the passages.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/agents.md`, *The seven agents*. The sentence "Six passages are v1.1's own text and not v1's" no longer gives a count. It says that the passages below are v1.1's own text and not v1's, and lists each one with the story that wrote it. The list keeps the six it names today: the sentence before the reviewer's checklist, the checklist's sixth item and the acceptance reviewer's added sentence in its check 6 (F0016-S0002); the reviewer's `Notes:` from round 1 on and its added criterion (F0021-S0005); and its correction of a stale Description (F0034-S0001). It adds R14's write-guard sentences (F0019-S0006), R15 (F0022-S0002), the acceptance reviewer's disk comparison in check 7 (F0012-S0017), and its check 3 *Mutation testing* with the words F0031-S0001 changed around it. It adds any other passage that the Interface's `git log` shows. *Replaced from v1*: the renaming table's lead-in says "except the passages of v1.1's own text that *The seven agents* names", with no number. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, since none of them counts the passages.

## Smoke test

```bash
grep -c -E '(Three|Six|Seven|Eight|Nine|Ten|three|six|seven|eight|nine|ten) passages' docs/project-guide/agents.md
```
Expect: `0`

```bash
for s in F0019-S0006 F0022-S0002 F0012-S0017 F0031-S0001 F0021-S0005 F0034-S0001; do grep -q -F "$s" docs/project-guide/agents.md && echo "named: $s" || echo "missing: $s"; done
```
Expect: six lines, `named: F0019-S0006`, `named: F0022-S0002`, `named: F0012-S0017`, `named: F0031-S0001`, `named: F0021-S0005`, `named: F0034-S0001`

## Journal
