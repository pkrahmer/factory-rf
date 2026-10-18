"""The todo demo's `secrets` recipe and the template's are one and the same."""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FILTER = (
    "\tfiles=$$(printf '%s\\n' $$files"
    " | grep -vE '^(uv\\.lock|\\.secrets\\.baseline|.*\\.costs\\.jsonl)$$' || true)"
)


def _secrets_recipe(makefile: Path) -> list[str]:
    lines = makefile.read_text(encoding="utf-8").splitlines()
    heads = [index for index, line in enumerate(lines) if re.match(r"^secrets\s*:", line)]
    assert len(heads) == 1, makefile
    recipe = []
    for line in lines[heads[0] + 1 :]:
        if not line.startswith("\t"):
            break
        recipe.append(line)
    return recipe


def test_the_todo_demos_secrets_target_is_the_templates() -> None:
    template = _secrets_recipe(ROOT / "template" / "Makefile")
    demo = _secrets_recipe(ROOT / "demo" / "todo-service" / "project" / "Makefile")

    assert demo == template
    assert FILTER in template
