#!/usr/bin/env bash
set -ev

# Replace the placeholders in configuration files with actual values
CONFIG="${GITHUB_WORKSPACE}/.github/aiida"
sed -i "s|PLACEHOLDER_BACKEND|${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_PROFILE|test_${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_DATABASE_NAME|test_${AIIDA_TEST_BACKEND}|" "${CONFIG}/profile.yaml"
sed -i "s|PLACEHOLDER_REPOSITORY|/tmp/test_repository_test_${AIIDA_TEST_BACKEND}/|" "${CONFIG}/profile.yaml"

verdi setup --config "${CONFIG}/profile.yaml"

verdi profile setdefault test_${AIIDA_TEST_BACKEND}
