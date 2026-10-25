"""Only the kernel guard's own modules still name the start wrapper or import its rules."""

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "src" / "factory"
GUARD_MODULES = {"factory.entry.confine", "factory.adapters.landlock", "factory.domain.confinement"}
GUARD_IMPORTS = {"factory.domain.confinement", "factory.adapters.landlock"}


def _module_name(path: Path) -> str:
    parts = path.relative_to(SOURCE.parent).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _imports(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def test_only_the_guard_s_modules_name_the_wrapper_or_import_its_rules() -> None:
    offenders: list[str] = []
    for path in sorted(SOURCE.rglob("*.py")):
        name = _module_name(path)
        text = path.read_text(encoding="utf-8")
        if name == "factory.entry.wiring" and "factory-confine" in text:
            offenders.append(f"{name}: factory-confine")
        if name in GUARD_MODULES:
            continue
        offenders.extend(
            f"{name}: {word}" for word in ("factory-confine:", "CLAUDE_CONFIG_DIR") if word in text
        )
        offenders.extend(
            f"{name}: imports {imported}"
            for imported in sorted(_imports(ast.parse(text)) & GUARD_IMPORTS)
        )

    assert offenders == []
