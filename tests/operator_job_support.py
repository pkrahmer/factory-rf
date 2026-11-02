"""What the tests of the operator's job script share: the job, its site values, a call's words."""

JOB = "factory-job"
IMPERSONATE = "deployer@p1.iam.gserviceaccount.com"
# The site values every command of the job script needs.
BARE = {"SITE_PROJECT": "p1", "SITE_REGION": "europe-west3", "SITE_JOB": JOB}


def words(call: list[str]) -> list[str]:
    """The words of a call that are no flag, in order."""
    return [word for word in call if not word.startswith("-")]
