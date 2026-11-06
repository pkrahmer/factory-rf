"""The missing lines and the time line of the document check tests."""

TOPIC_FILES = (
    "install.md",
    "agent-runtime.md",
    "machine.md",
    "site.md",
    "cloud-run.md",
    "health.md",
    "stops.md",
    "pipeline.md",
    "records.md",
    "work-items.md",
)
MISSING_LINES = (
    "README.md: missing\n"
    "docs/operator-guide/README.md: missing\n"
    + "".join(f"docs/operator-guide/{name}: missing\n" for name in TOPIC_FILES)
    + "docs/project-guide/README.md: missing\n"
    "docs/decisions.md: missing\n"
)
TIME_LINE = r"documents ok \(\d+(\.\d+)? s\)"
