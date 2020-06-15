import json
import os
import re
from typing import Union
import sys

import requests


REPOSITORY_URL = (
    "https://api.github.com/repos/Materials-Consortia/optimade-python-tools"
)


def get_json(request: requests.Response) -> Union[dict, list]:
    """Utility function to 'safely' get JSON from response"""
    try:
        response: Union[dict, list] = request.json()
    except json.JSONDecodeError:
        sys.exit(
            f"Could not decode '{request.url}'. Status code: {request.status_code}"
        )
    else:
        return response


# Check current GitHub ref is a valid version tag
GITHUB_REF = os.environ.get("GITHUB_REF", None)

if GITHUB_REF is None:
    sys.exit("Could not retrieve current GitHub ref from environment variable")

if re.match(r"refs/tags/v[0-9]+(\.[0-9]+){2}$", GITHUB_REF) is None:
    sys.exit(
        f"You are NOT publishing a tag with the correct name format (vMAJOR.MINOR.PATCH), but instead '{GITHUB_REF}', will shut the publishing workflow down"
    )


# Get latest release (latest tag)
all_tags: list = get_json(requests.get(f"{REPOSITORY_URL}/tags"))
latest_release: str = sorted([tag.get("name", "v0.0.0") for tag in all_tags])[-1]


# Get commit date and time for latest release
latest_release_commit: dict = get_json(
    requests.get(f"{REPOSITORY_URL}/commits/{latest_release}")
)
latest_release_datetime: Union[str, None] = latest_release_commit.get("commit", {}).get(
    "committer", {}
).get("date", None)

if latest_release_datetime is None:
    sys.exit(
        f"Could not retrieve the datetime for the latest release commit:\n\n{json.dumps(latest_release_commit, indent=2)}"
    )


# Get list of all commits since latest release in `master`
master_commits: list = get_json(
    requests.get(f"{REPOSITORY_URL}/commits?since={latest_release_datetime}")
)
master_commit_shas = [commit.get("sha", "") for commit in master_commits]


# Check current GitHub SHA is already in the `master` branch
GITHUB_SHA = os.environ.get("GITHUB_SHA", None)

if GITHUB_SHA is None:
    sys.exit("Could not retrieve current GitHub SHA from environment variable")

if GITHUB_SHA not in master_commit_shas:
    sys.exit(
        "You are NOT publishing a tag pointing to a commit in the `master` branch, will shut the publishing workflow down"
    )

print(
    "All seems to be in order:\n"
    f"The published tag has the correct type of name (vMAJOR.MINOR.PATCH: {GITHUB_REF[len('refs/tags/'):]}) and refers to an existing commit in the `master` branch: {GITHUB_SHA}."
)
sys.exit(0)
