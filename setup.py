import os
import json

from setuptools import setup, find_packages

module_dir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    with open(os.path.join(module_dir, "setup.json"), "r") as info:
        setup_json = json.load(info)

    setup_json["extras_require"]["testing"] = set(
        setup_json["extras_require"]["testing"]
        + setup_json["extras_require"]["django"]
        + setup_json["extras_require"]["elastic"]
    )

    setup_json["extras_require"]["all"] = list(
        {item for sublist in setup_json["extras_require"].values() for item in sublist}
    )

    setup_json["tests_require"] = list(setup_json["extras_require"]["testing"])

    setup(
        packages=find_packages(),
        long_description=open(os.path.join(module_dir, "README.md")).read(),
        long_description_content_type="text/markdown",
        **setup_json
    )
