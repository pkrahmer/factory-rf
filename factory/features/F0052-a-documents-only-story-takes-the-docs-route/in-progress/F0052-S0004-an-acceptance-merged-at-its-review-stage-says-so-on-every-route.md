# An acceptance merged at its review stage says so on every route

## Description

The human may merge an acceptance's pull request while the acceptance reviewer still works, and the operator guide promises that the `done` entry then says `done (pull request merged before approval); cost: ...` (`docs/operator-guide/work-items.md`, *Merged before its approval*). `AcceptanceMerged` asks `is_before_approval(definition, stage)` (`factory.work.domain.acceptance`) for this. Today that function compares the stage's position with the position of the definition's *first* approval stage. The shipped `factory/pipeline.yml` now lists `docs-approval` before `acceptance`, so `is_before_approval(definition, "acceptance")` is `False`, and an early merge of an acceptance gets the ordinary entry, which breaks the guide's promise. This story makes the function follow the stage's forward moves instead: a stage lies before the approval when its chain of first `next` entries reaches an approval stage. The order of the stages in the file then no longer matters. The booking, the merge handling and the pipeline definition stay as they are.

## Interface

- `factory.work.domain.acceptance` (domain), signature unchanged:

  ```python
  def is_before_approval(definition: PipelineDefinition, stage: str) -> bool:
      """Whether `stage` leads to an approval stage by its forward moves."""
  ```

  - A `stage` that is not in `definition.stages` raises `KeyError` (unchanged).
  - A definition without any stage with `approval: true` raises `ValueError` (unchanged).
  - An approval stage gives `False`. A stage without `next` (`done`) gives `False`.
  - Any other stage: follow `next[0]` from `stage`. The result is `True` when the chain reaches an approval stage. It is `False` when the chain reaches a stage without `next` or a stage it has already visited (a loop), without hanging.
- `tests/work/domain/test_acceptance_before_approval_routes.py` (new): the table on a definition of the shipped order and the loop and dead-end cases.
- `tests/work/application/test_acceptance_merged_on_two_routes.py` (new): the early merge in the fake world on a definition of the shipped order.
- An earlier test this story changes: `tests/pipeline/application/test_docs_route.py::test_only_the_docs_routes_working_stages_lie_before_the_approval`, row `acceptance` from `False` to `True`. Feature decision 7 gives the leave for this row.

## Acceptance criteria

1. On a definition with the stages of the shipped `factory/pipeline.yml`, in its order (`intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, `docs-only`, `docs-review`, `docs-approval`, `acceptance`, `approval`, `done`), `is_before_approval` is `True` for `intake`, `tests`, `doing`, `review`, `docs`, `smoke-test`, `docs-only`, `docs-review` and `acceptance`, and `False` for `docs-approval`, `approval` and `done`. There is one row per stage.
2. On the single-route definition of `tests/work/domain/test_acceptance_before_approval.py`, the results do not change: `acceptance` is `True`, and `approval` and `done` are `False`.
3. A stage whose forward chain loops (`a` with `next: [b]`, `b` with `next: [a]`, beside an approval stage that neither reaches) gives `False`. A stage whose forward chain ends at `done` without an approval stage gives `False`. A stage whose chain reaches the approval stage after three moves gives `True`. Each case is one row of one parametrized test.
4. An unknown stage raises `KeyError`, and a definition without an approval stage raises `ValueError`. Each is one row.
5. In the fake world, on a definition of the shipped order, an acceptance that the human merges while it is at `acceptance` is booked `accepted` with the entry `done (pull request merged before approval); cost: ...`. One merged at `approval` gets the ordinary `done (pull request merged); cost: ...` entry. Each is one row.
6. `make check` stays green.
7. docs: `docs/project-guide/pipeline.md`, *More than one route, more than one approval stage*: `is_before_approval` follows the first `next` of each stage, so the order of the stages in the file does not matter to it; the sentence that every route's stages must be listed before the first approval stage goes. `docs/operator-guide/work-items.md`: none, because it then holds true again. `docs/decisions.md`: one entry. It says that "before the approval" is read from the forward moves, not from the position. The reason is that the docs route lists `docs-approval` before `acceptance`. Rejected: reordering `factory/pipeline.yml` so that every approval stage comes last. That would put a rule into the file's order that nothing checks.

## Smoke test

```bash
uv run python -c "from pathlib import Path; from factory.pipeline.adapters.pipeline_yaml import RuamelPipelineDefinitionReader; from factory.work.domain.acceptance import is_before_approval; d = RuamelPipelineDefinitionReader().parse(Path('factory/pipeline.yml').read_text()); print(is_before_approval(d, 'acceptance'), is_before_approval(d, 'docs-review'), is_before_approval(d, 'docs-approval'))" 2>&1 | tail -1
```
Expect: `True True False`

## Journal
