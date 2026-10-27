"""The login file and hint of the agent run probe's login tests."""

from pathlib import Path

LOGIN_FILE = Path("/home/agent/.claude-token")


HINT = (
    "; the agent's login token is read from /home/agent/.claude-token: "
    "make it with claude setup-token if it is missing, empty or expired"
)
