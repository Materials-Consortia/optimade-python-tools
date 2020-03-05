#!/bin/bash
# Note: This returns exit code 0, if the two specs agree, otherwise exit code 1
docker run -t -v $1:/specs:ro quen2404/openapi-diff /specs/openapi/openapi.json /specs/openapi/local_openapi.json
