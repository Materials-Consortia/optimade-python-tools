#!/usr/bin/env bash
# Bash script to run upon starting the Dockerfile.
#
# Any extra parameters supplied to this script will be passed on to `uvicorn`.
# This is can be nice if using the image for development (adding `--reload` and more).
set -e

if [ "${OPTIMADE_CONFIG_FILE}" == "/app/optimade_config.json" ]; then
    echo "Using the demo config file."
    echo "Set the environment variable OPTIMADE_CONFIG_FILE to override this behaviour."
    echo "For more configuration options, please see https://www.optimade.org/optimade-python-tools/configuration/."
    echo "Note, the variable should point to a bound path within the container."
fi

if [ -z "${OPTIMADE_LOG_LEVEL}" ]; then
    export OPTIMADE_LOG_LEVEL=info
fi

if [ "${OPTIMADE_DEBUG}" == "1" ]; then
    export OPTIMADE_LOG_LEVEL=debug
fi

# Determine the server to run (standard or index meta-db)
if [ -z "${MAIN}" ] || ( [ "${MAIN}" != "main_index" ] && [ "${MAIN}" != "main" ] ); then
    MAIN="main"
fi

uvicorn optimade.server.${MAIN}:app --host 0.0.0.0 --port 5000 --log-level ${OPTIMADE_LOG_LEVEL} "$@"
