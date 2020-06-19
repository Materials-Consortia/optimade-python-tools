#!/bin/sh
set -e

echo "-o- Checkout fresh branch -o-"
git checkout -b update_changelog

echo "-o- Setting commit user -o-"
git config --local user.email "dev@optimade.org"
git config --local user.name "OPTIMADE Developers"

echo "-o- Install current SHA (optimade) -o-"
pip install -U -e .[dev]
pip install -r requirements-docs.txt

echo "-o- Update version -o-"
# invoke setver -v ${GITHUB_REF#refs/tags/}
invoke setver -v "0.10.0"

echo "-o- Generate new OpenAPI JSON files -o-"
pip install -U -e .[dev]
invoke update-openapijson

echo "-o- Generate changelog -o-"
apt-get update
apt-get -y install ruby-full
export GEM_HOME="${HOME}/gems"
export PATH="${GEM_HOME}/bin:${PATH}"
gem install github_changelog_generator
github_changelog_generator --user "Materials-Consortia" --project "optimade-python-tools" --token ${INPUT_TOKEN}

echo "-o- Overwrite old CHANGELOG.md -o-"
mv -f CHANGELOG.md docs/

echo "-o- Commit updates -o-"
git add setup.py
git add openapi/index_openapi.json openapi/openapi.json
git add docs/CHANGELOG.md
# git commit -m "Releasing ${GITHUB_REF#refs/tags/}"
git commit -m "Releasing v0.10.0"
