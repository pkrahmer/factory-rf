# Decisions

The log of lasting decisions: what was decided, why, and what was rejected. Newest last. The first entries are the seed's choices (2026-10-12); the stories' decisions follow.

## The package is `factory`, in four layers

The code is one package, `src/factory/`, with the layers `factory.domain`, `factory.application`, `factory.adapters` and `factory.entry`. A higher layer may import a lower one (import-linter, `make layers`, part of `make check`). The project is named `factory-rf`; the package carries the factory's own name.

## Three top-level paths for the product beyond `src/` and `tests/`

`image/` (Dockerfile, compose file, entrypoint), `template/` (v1.1's own project template) and `claude/` (the agent and skill files v1.1 ships). The coder's write paths in `factory/stages.yml` name them; the folders are created by the stories that need them. `Makefile`, `pyproject.toml`, `uv.lock`, the import-linter configuration, `CLAUDE.md` and `factory/` stay outside every write path.

## No `mutants` target, no mutmut

The acceptance reviewer runs `make mutants` only when it exists. Over the whole package it could outgrow the 60-minute lease in later features, and a timeout is a stall. So the seed has neither the target nor the dependency.

## The licence allow list has one LGPL entry and one dual-licence entry

PyGithub is LGPL-3.0, and `pip-licenses` reports it as `GNU Library or Lesser General Public License (LGPL)`, which is now on the allow list. `cryptography` (a transitive runtime dependency, through PyGithub) is reported as `Apache-2.0 OR BSD-3-Clause`, which is also allowed. The template's list is otherwise unchanged.

## The project guide lives in `docs/`

`docs/project-guide.md` is the guide for agents (R17). It is in `docs/` and not in `CLAUDE.md` so that the documenter, whose write paths are `README.md` and `docs/*`, can keep it true; `CLAUDE.md` stays the human's, and points to the guide.
