#!/bin/bash
set -ex

if [ "$1" == "index" ]; then
    MAIN="main_index"
    PORT=5001
else
    if [ "${MAIN}" == "main_index" ]; then
        PORT=5001
    else
        MAIN="main"
        PORT=5000
    fi
fi

uvicorn optimade.server.$MAIN:app --reload --port $PORT
