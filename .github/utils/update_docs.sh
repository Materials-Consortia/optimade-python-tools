#!/usr/bin/env bash
set -e

echo -e "\n-o- Setting commit user -o-"
git config --global user.email "${GIT_USER_EMAIL}"
git config --global user.name "${GIT_USER_NAME}"

echo -e "\n-o- Update 'API Reference' docs -o-"
invoke create-api-reference-docs --pre-clean

echo -e "\n-o- Commit update - API Reference -o-"
git add docs/api_reference
if [ -n "$(git status --porcelain docs/api_reference)" ]; then
    # Only commit if there's something to commit (git will return non-zero otherwise)
    git commit -m "Release ${GITHUB_REF#refs/tags/} - API Reference"
fi

echo -e "\n-o- Update version -o-"
invoke setver --ver="${GITHUB_REF#refs/tags/}"

echo -e "\n-o- Commit updates - Version & Changelog -o-"
git add optimade/__init__.py docs/static/default_config.json
git add openapi/index_openapi.json openapi/openapi.json
git add CHANGELOG.md
git commit -m "Release ${GITHUB_REF#refs/tags/} - Changelog"

echo -e "\n-o- Update version tag -o-"
TAG_MSG=.github/utils/release_tag_msg.txt
sed -i "s|TAG_NAME|${GITHUB_REF#refs/tags/}|" "${TAG_MSG}"
git tag -af -F "${TAG_MSG}" ${GITHUB_REF#refs/tags/}
