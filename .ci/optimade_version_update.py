import json
import sys
from configparser import ConfigParser
from pathlib import Path

shields_json = Path(__file__).resolve().parent.joinpath("optimade-version.json")
config_ini = (
    Path(__file__).resolve().parent.parent.joinpath("optimade/server/config.ini")
)

with open(shields_json, "r") as fp:
    shield = json.load(fp)

config = ConfigParser()
config.read(config_ini)

shield_version = shield["message"]
current_version = f'v{config.get("IMPLEMENTATION", "API_VERSION")}'

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
