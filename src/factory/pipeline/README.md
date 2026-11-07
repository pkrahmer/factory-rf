# The pipeline area

The pipeline definition, the stages, the tick and its handlers, claims, stops and recovery. [The guide page](../../../docs/project-guide/pipeline.md) explains it.

- `adapters/` The reader of the pipeline definition, YAML.
- `application/` The use cases: the claim, the stage, the take, the tick with its handlers, stalls, stops and the boundaries.
- `domain/` The rules of the pipeline definition, leases, checks, stops, recovery, events and the evaluation.
