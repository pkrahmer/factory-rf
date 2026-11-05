"""The factory log's line for a run that died: the run, its work item and stage, and its text."""


def died_line(run: str, work_item: str, stage: str, text: str) -> str:
    """The line that names the died `run` of `work_item` in `stage` and quotes its `text`."""
    return f"run {run} of {work_item} ({stage}) died: {text}"
