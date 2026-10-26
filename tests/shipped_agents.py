"""The seven agents the factory ships: their front matter values and the opening of their bodies."""

from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import RuamelYamlHandler, split_front_matter
from factory.domain.pipeline_definition import PipelineDefinition

ROOT = Path(__file__).parent.parent
AGENT_HOME = ROOT / "claude"
TEMPLATE_PIPELINE = ROOT / "template" / "factory" / "pipeline.yml"

_ALL_TOOLS = ["Read", "Grep", "Glob", "Edit", "Bash", "Write", "Skill"]
_TOOLS_WITHOUT_WRITE = ["Read", "Grep", "Glob", "Edit", "Bash", "Skill"]


class ShippedAgent(BaseModel):
    """One shipped agent as its file must hold it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    model: str
    effort: str
    budget_usd: Decimal
    tools: list[str]
    boundary: str
    entry: str


SHIPPED_AGENTS = [
    ShippedAgent(
        name="intake",
        model="sonnet",
        effort="low",
        budget_usd=Decimal("1"),
        tools=_TOOLS_WITHOUT_WRITE,
        boundary="You do not improve the story; you accept it or ask.",
        entry=(
            "Your entry starts with `accepted` and then has one line for each of the Interface, "
            "the criteria, the smoke test, the architecture and the scope; or it is the numbered "
            "questions, with the form's findings among them."
        ),
    ),
    ShippedAgent(
        name="tester",
        model="opus",
        effort="medium",
        budget_usd=Decimal("2"),
        tools=_ALL_TOOLS,
        boundary=(
            "You test what the criteria say and nothing else; a case they leave open is a question."
        ),
        entry=(
            "Your entry maps each criterion to its test function, one line each, and names the "
            "files you created and any module the test run could not import."
        ),
    ),
    ShippedAgent(
        name="coder",
        model="opus",
        effort="medium",
        budget_usd=Decimal("4"),
        tools=_ALL_TOOLS,
        boundary="Never edit tests; a wrong test is a question.",
        entry=(
            "Your entry says what you built (the paths), the main choice and the alternative you "
            "rejected, and what you noticed but did not touch."
        ),
    ),
    ShippedAgent(
        name="reviewer",
        model="opus",
        effort="high",
        budget_usd=Decimal("3"),
        tools=_TOOLS_WITHOUT_WRITE,
        boundary="You find and do not fix: you write no code, not even scratch.",
        entry=(
            "Your entry is the numbered findings, each with a location, what is wrong and what "
            "would fix it, or `no findings`."
        ),
    ),
    ShippedAgent(
        name="documenter",
        model="sonnet",
        effort="medium",
        budget_usd=Decimal("1.5"),
        tools=_ALL_TOOLS,
        boundary=(
            "You write for a reader who was not there; you edit no code, no test and no comment "
            "in code."
        ),
        entry=(
            "Your entry names each file you changed and why, the documents you cross-read and "
            "found current, and stale text you noticed that is not yours to fix."
        ),
    ),
    ShippedAgent(
        name="smoke-tester",
        model="opus",
        effort="medium",
        budget_usd=Decimal("2"),
        tools=_TOOLS_WITHOUT_WRITE,
        boundary="Fix nothing: run the smoke test as written and report what you observe.",
        entry=(
            "Your entry gives each command's output trimmed to 40 lines and whether it met its "
            "`Expect:` line, and numbers the findings."
        ),
    ),
    ShippedAgent(
        name="acceptance-reviewer",
        model="opus",
        effort="high",
        budget_usd=Decimal("8"),
        tools=_ALL_TOOLS,
        boundary=(
            "You propose backlog stories and never start one; you change nothing but your report "
            "and those stories."
        ),
        entry=(
            "Your entry starts with your recommendation and the number of backlog stories you "
            "propose, then has one line for each item you judged."
        ),
    ),
]

SHIPPED_NAMES = [agent.name for agent in SHIPPED_AGENTS]

WRITE_PATHS_RULE = (
    "R14. The pipeline's own files — `factory/pipeline.yml`, `factory/story-form.md`, every "
    "feature's `feature.md`, `backlog/`, `done/` and `.claude/` — change only with the human's "
    "commit or on their explicit instruction. You write only within your write paths in the "
    "pipeline definition (`{work_item}` there is your own work item, outside its front matter and "
    "journal), nothing else: after the stage the factory takes only the changed paths your role "
    "may write and leaves every other change out, whatever tool or command made it, so a write "
    "elsewhere is lost. When the work needs a path outside your write paths, end with `question` "
    "and name it. Make temporary files with `mktemp` or `tempfile`; they are lost with the stage."
)


def front_matter_and_body(name: str) -> tuple[str, str]:
    """The raw front matter and the stripped body of the shipped agent file `name`."""
    text = (AGENT_HOME / "agents" / f"{name}.md").read_text(encoding="utf-8")
    split = split_front_matter(RuamelYamlHandler(), text)
    assert split is not None
    front_matter, body = split
    return front_matter, body.strip()


def agent_body(name: str) -> str:
    """The stripped body of the shipped agent file `name`."""
    _, text = front_matter_and_body(name)
    return text


def template_definition() -> PipelineDefinition:
    """The pipeline definition the template ships, parsed by the factory's reader."""
    return RuamelPipelineDefinitionReader().parse(TEMPLATE_PIPELINE.read_text(encoding="utf-8"))
