#!/bin/bash

export OPTIMADE_LOG_LEVEL=info
if [ "$1" == "debug" ]; then
    export OPTIMADE_DEBUG=1
    export OPTIMADE_LOG_LEVEL=debug
fi

if [ "$1" == "index" ]; then
    MAIN="main_index"
    PORT=5001
    if [ "$2" == "debug" ]; then
        export OPTIMADE_DEBUG=1
        export OPTIMADE_LOG_LEVEL=debug
    fi
else
    if [ "${MAIN}" == "main_index" ]; then
        PORT=5001
    else
        MAIN="main"
        PORT=5000
    fi
fi

uvicorn optimade.server.$MAIN:app --reload --port $PORT --log-level $OPTIMADE_LOG_LEVEL
