"""A pipeline definition of two routes to two approval stages, in the shipped order."""

from typing import Final

TWO_ROUTES: Final[str] = """\
contract: "1.0"
attempts_cap: 2
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 8}
  lint: {time_limit: 5}
  test: {time_limit: 10}
  duplicates: {time_limit: 2}
  documents: {time_limit: 2}
  secrets: {time_limit: 3}
  sync: {time_limit: 5}
roles:
  intake: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  tester: {write_paths: ["tests/*"], time_limit: 40, lease_duration: 60}
  coder: {write_paths: ["src/*"], time_limit: 40, lease_duration: 60}
  reviewer: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  documenter: {write_paths: ["README.md", "docs/*"], time_limit: 40, lease_duration: 60}
  smoke-tester: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  acceptance-reviewer:
    write_paths: ["{work_item}", "{feature}/backlog/*"]
    time_limit: 40
    lease_duration: 60
stages:
  intake: {role: intake, next: [tests, docs-only]}
  tests: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review, tests], checks: [check], reports: [duplicates]}
  review: {role: reviewer, next: [docs, doing], round_cap: 2}
  docs:
    role: documenter
    next: [smoke-test, doing]
    checks: [check, secrets, documents]
    round_cap: 2
  smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 2}
  docs-only: {role: documenter, next: [docs-review, tests], checks: [check, secrets, documents]}
  docs-review: {role: reviewer, next: [docs-approval, docs-only], round_cap: 2}
  docs-approval: {approval: true, next: [done, docs-only]}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""
