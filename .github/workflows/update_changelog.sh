#!/bin/sh
set -e

echo "\n-o- Checkout fresh branch -o-"
git checkout -b update_changelog

echo "\n-o- Setting commit user -o-"
git config --local user.email "dev@optimade.org"
git config --local user.name "OPTIMADE Developers"

echo "\n-o- Install current SHA (optimade) -o-"
pip install -U -e .[server]
pip install invoke jsondiff

echo "-o- Update version -o-"
# invoke setver -v ${GITHUB_REF#refs/tags/}
echo "Will actually be the tag name: ${GITHUB_REF#refs/tags/}, but is now 0.10.1"
invoke setver -v "v0.10.2"

echo "\n-o- Generate changelog -o-"
apt-get update
apt-get -y install ruby-full
export GEM_HOME="${HOME}/gems"
export PATH="${GEM_HOME}/bin:${PATH}"
gem install github_changelog_generator
github_changelog_generator --user "Materials-Consortia" --project "optimade-python-tools" --token ${INPUT_TOKEN}

echo "\n-o- Overwrite old CHANGELOG.md -o-"
mv -f CHANGELOG.md docs/

echo "\n-o- Commit updates -o-"
git add optimade/__init__.py
git add openapi/index_openapi.json openapi/openapi.json
git add docs/CHANGELOG.md
git commit -m "Release ${GITHUB_REF#refs/tags/} (test, using 0.10.2)"
