#!/bin/bash

if [ "$1" == "debug" ]; then
    export DEBUG=1
fi

if [ "$1" == "index" ]; then
    MAIN="main_index"
    PORT=5001
    if [ "$2" == "debug" ]; then
        export DEBUG=1
    fi
else
    if [ "${MAIN}" == "main_index" ]; then
        PORT=5001
    else
        MAIN="main"
        PORT=5000
    fi
fi

uvicorn optimade.server.$MAIN:app --reload --port $PORT
