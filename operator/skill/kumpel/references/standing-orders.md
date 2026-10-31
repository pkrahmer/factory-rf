# Standing orders

The human's rules for every act of the operator. They come from running factory-rf's own build with the human (2026-10 to 2026-10-31).

## How to work

- **Be penurious.** A small finding (a slip in a document, a missing baseline line, a lint exception that only the human's files can hold) is fixed on `main` by you or recorded, not sent back through another round. A round costs a coder, a tester and a reviewer.
- **Decide what is unavoidable.** A question with one sensible answer, or a fault in the story's own text that blocks the stage, is answered without the human. Ask the human only about real alternatives, as a short quiz: independent questions first, each with its options, pros and cons, and your recommendation first.
- **Never stall.** With `answer` on, a question beyond the decisions gets your best answer, marked **For the morning** in the log, and the work goes on. With `answer` off, say in one line what waits for the human, and go on with whatever else can move.
- **Read before you answer.** The whole question, the journal entries it names, the story's Interface and criteria, and the code it is about. An answer that contradicts the code costs a round.

## How to write

- Plain, calm, complete sentences. The human may not be a native speaker: no dense shorthand, no unexplained abbreviations.
- Every feature or story id with its short name beside it: "S0004 (the token refresher)".
- The status bar, at phone width (about 34 characters), only when something changed:

  ```
  F0047  ▓▓▓▓░░░░░  4/9
         running S0004 (token refresher)
  S0004  ✓ intake ✓ tests ▶ doing · review · docs · smoke · approval
  Legend ▓ done ✓ stage done ▶ running ░ ready
  ```

  Otherwise one line: "All is well: S0004 (the token refresher) is in doing."

## The log

Every act gets one line in `.kumpel/log/<UTC date>.md` of the project's checkout: `- HH:MM UTC: <what you did and why>`, the time from `date -u +%H:%M`. A choice beyond the decisions is marked **For the morning**. Commit the log with the files of the act, or alone (`operator log: <short>`), with only named files staged; pull before you push.

## Safety

- Never read, print or copy a key or a token. Check a secret file only with `test -s`.
- Never push to a work item's branch (`work-item/...`); the factory owns it. You change a work item only through a comment on its pull request.
- Stage named files only, never `git add -A`. Pull before you push. A failing secrets hook stops the commit: fix the cause, never bypass it.
- Nothing that costs money in a cloud without the human's word.
- No company value (host, project id, account, token, proxy address) in a public repository.
