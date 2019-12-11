#!/bin/bash
if [ "$1" == "index" ]
then
    MAIN="main_index"
    PORT=5001
else
    MAIN="main"
    PORT=5000
fi

uvicorn optimade.server.$MAIN:app --reload --port $PORT
