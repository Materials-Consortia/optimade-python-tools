#!/bin/bash
set -ex

if [ "${MAIN}" == "main_index" ]; then
    PORT=5001
else
    MAIN="main"
    PORT=5000
fi

uvicorn optimade.server.$MAIN:app --host 0.0.0.0 --port $PORT
