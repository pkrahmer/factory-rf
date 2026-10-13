# Brief: the quiz on the working answers and the interface sheet

## Goal

Write one questionnaire the human can answer in one sitting, in batches of up to four multiple-choice questions, without anyone preparing between batches. It covers every answer the main session took for the human during and after the overnight run that still binds work not yet built (F0002 to F0011), and the open points F0001's acceptances left for the human. The human did not see these answers being taken; the questionnaire is how they confirm or change them.

## Inputs (read these)

- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton-answers.md`: the working answers (skeleton questions 1–16, interface-sheet questions 1–14, drafting, F0001 rounds 1–2, cross-check blockers 1–3).
- `C:\Dev\Projects\factory-rf\planning\overnight\skeleton.md` ("Open questions") and `interfaces.md` ("Open questions", "Amendments during the night", and whichever DTO, interface or names section a question points at): what was asked and why.
- `C:\Dev\Projects\factory-rf\planning\overnight\cross-check-1.md`: the blockers and the should-fixes.
- `C:\Dev\Projects\factory-v2\planning\v1.1\handover.md` (sections 2, 4 and 5, and the appendix of names) and `C:\Dev\Projects\factory-v2\planning\decisions\001-*.md` to `007-*.md`: what the human already decided. An answer the human already decided is not asked again.
- `C:\Dev\Projects\factory-rf\factory\features\F0001-boundaries\FEATURE.md` (decisions 1–23) and `ACCEPTANCE.md` (sections 4, 5 and 6: the points left for the human).
- `C:\Dev\Projects\factory-rf\docs\decisions.md` and `C:\Dev\Projects\factory-rf\CLAUDE.md`.
- The format example: `C:\Dev\Projects\factory-v2\planning\questionnaires\02-after-vision.md`.

## Which questions

- Ask about every working answer that is a real choice and still shapes stories not yet built: name the stories or features it shapes (from `skeleton.md` and the drafts under `planning\overnight\stories\`).
- Do not ask about:
  - a fact that was checked, such as the container having no root or Docker (list it as settled);
  - something F0001 built and the human has since accepted, unless a later feature still depends on the choice;
  - something the human already decided in decisions 001–007, F0001's decisions 20–23 or `CLAUDE.md`.

  List each skipped answer in a closing section "Settled, not asked", one line each with the reason.
- F0001's open points from `ACCEPTANCE.md` sections 4–6: ask one question for each point of substance (examples: the hosting interface wider than R10, `set_labels` reading label names, decision 19's unsourced defaults, the pinned `claude` version, `version()`'s working directory). Gather the small tidy-ups into one question about how to handle them:
  - `RemoteBranch` not frozen;
  - the `*_protocol.py` test names;
  - `merge` checking its ref twice;
  - the control-character test row;
  - decision 16's "fourteen";
  - the three one-line doc remnants;
  - the long decision entry.

  Its options could be: one housekeeping story now, a commit by the human, folded into the next story that touches the file, or left as they are.
- Merge working answers that are one choice into one question. Aim for 15 to 30 questions in all.

## The form of each question

- A number and a short title, and the `header` the dialog shows (at most 12 characters).
- An explanation of two to six sentences, for a reader who knows the factory but did not see the night: what the question is about, why it came up, and what the working answer does now.
- The question itself, one sentence ending in `?`.
- Two to four options, each with a label of at most five words and a one- or two-line description that gives its pros and cons. The first option is the recommendation, marked "(Recommended)" at the end of its label. Usually it is the working answer; recommend another option only when you found a reason, and give that reason in the explanation.
- "If changed": the stories or drafts that would need editing if the human picks something other than the working answer.

## Order

- Round 1 holds only questions whose answers do not depend on one another, grouped by theme (lease and crashes, posts and the hosting service, files and names, git and agents, F0001 leftovers).
- Later rounds hold questions that depend on an earlier answer, each naming the question it depends on and saying what to ask for each possible earlier answer.
- Number the batches of up to four in the order they should be asked.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\questionnaires\01-working-answers.md`, holding:

- a short introduction;
- the rounds and their batches;
- "Settled, not asked";
- an empty "Answers" section for the session to fill in.

## Not

- No git commands. No file other than the output. Do not change the working answers, the drafts or any decision.

## Reply

At most 15 lines: the number of questions per round, the questions where you recommend something other than the working answer (one line each, with the reason), and anything you could not turn into a choice.

Model: opus.
