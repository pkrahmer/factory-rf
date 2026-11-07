# The hosting area

Git, the hosting service, pushes, the hand-over and the opening of pull requests. [The guide page](../../../docs/project-guide/hosting.md) explains it.

- `adapters/` The git command-line wrapper, the PyGithub client, the fake hosting service and the test fixtures.
- `application/` The git and hosting-service interfaces, pushes and the opening of a work item.
- `domain/` The data of git and the hosting service, the hand-over and the texts the factory posts.
