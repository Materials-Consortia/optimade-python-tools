#!/bin/bash
# Note: This returns exit code 0, if the two specs agree, otherwise exit code 1
docker run -t -v $(pwd):/specs:ro quen2404/openapi-diff /specs/openapi.json /specs/local_openapi.json
