import json
import sys
from pathlib import Path

try:
    from optimade import __api_version__
except ImportError:
    raise ImportError(
        "optimade needs to be installed prior to running 'optimade_version_update.py'"
    )

shields_json = Path(__file__).resolve().parent.joinpath("optimade-version.json")

with open(shields_json, "r") as fp:
    shield = json.load(fp)

shield_version = shield["message"]
current_version = f"v{__api_version__}"

if shield_version == current_version:
    # The shield has the newest implemented version
    print(
        f"""They are the same: {current_version}
Shield file:
{json.dumps(shield, indent=2)}"""
    )
    sys.exit(0)

print(
    f"""The shield version is outdated.
Shield version: {shield_version}
Current version: {current_version}
"""
)

shield["message"] = current_version
with open(shields_json, "w") as fp:
    json.dump(shield, fp, indent=2)
    fp.write("\n")

# Check file was saved correctly
with open(shields_json, "r") as fp:
    updated_shield = json.load(fp)

if updated_shield["message"] == current_version:
    print(f"Successfully updated the shield version to '{updated_shield['message']}'")
    sys.exit(0)
else:
    print(
        f"""Something went wrong !
Shield file:
{json.dumps(updated_shield, indent=2)}"""
    )
    sys.exit(1)
