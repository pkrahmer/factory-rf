# Shaping stories and features

Only when the human asks. A feature is `factory/features/F<nnnn>-<slug>/feature.md` with its stories in `backlog/`; the forms are `factory/story-form.md` and `factory/feature-form.md` (where the project has one).

## Reviewing a draft

1. Run the form check on every story: `factory-check-story <path>` from the checkout's root (it prints nothing but `ok` lines when the form holds).
2. Read each story against the code it touches. The commonest faults found on 2026-10-31: an Interface that breaks the layer rule (the application layer calling an adapter); a smoke test that builds an object the Interface later changes; an Interface rule no criterion tests (each side of every limit needs a row); a default that lets code from an unreviewed branch run somewhere it should not; a value only the real environment can show, guessed instead of measured.
3. Check the feature's decisions against each other and against the stories' text; a decision a story contradicts is a finding.
4. Report: what holds, what must change before building, what you accept as decided; quiz the human only on real alternatives.

## Drafting

Follow the forms. One story is one coder's forty minutes; split where a layer is built on another. Every option off by default where the feature adds behaviour beside an existing one. Each story's first criterion is the unchanged default. Name in the feature the human's changes outside every write path, and the leaves the stories need.

## Small fixes

A story still in `backlog/` may be corrected on `main` (run the form check again, commit with the reason). A story in progress is changed only through an answer on its pull request.
