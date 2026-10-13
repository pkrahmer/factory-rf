# Operator guide

The guide for the person who runs the factory this repository implements: how to install it, how to configure it, which stops it can reach and what to do about each. Nothing is built yet, so there is nothing to install or configure. The documenter stage fills this in from the stories' docs criteria.

## The project's make targets

The factory runs a project's build through make and calls three targets: `check` (the full gate, which must be green before a stage hands forward), `lint` (run after the tester stage) and `test`. A project must define them in the Makefile at the root of its checkout. Each is judged by its exit status alone, and a target that does not exist counts as a failed command. A target that runs past its time limit is killed and counts as failed for that reason; the factory reads only the exit status, the last line and the last 30 lines of the output.

## The agent runtime

The factory runs each agent as a `claude -p` call under your own `claude` login: it needs the `claude` program and a session you have already logged in to, and it holds no API key of its own. The call gets only the environment the run's request gives, with no variable inherited from the factory. The flags are those of v1 and have not yet been checked against the pinned `claude` version (WE6.3). If a call fails at once, check them first. A run that dies, runs past its time limit or returns no usable decision stops the story as a stall; the cost and tokens of a timed-out run are shown as unknown.
