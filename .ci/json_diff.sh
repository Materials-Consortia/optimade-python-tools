#!/bin/bash
invoke generate-openapi

diff=$(jsondiff ./openapi/openapi.json ./openapi/local_openapi.json);
index_diff=$(jsondiff ./openapi/index_openapi.json ./openapi/local_index_openapi.json);

if [ ! "$diff" = "" ] && [ ! "$diff" = "{}" ] ; then
    echo -e "Generated OpenAPI spec for test server did not match committed version.\nRun 'invoke update-openapijson' and re-commit.\nDiff:\n$diff";
exit 1;
fi

if [ ! "$index_diff" = "" ] | [ ! "$index_diff" = "" ]; then
    echo -e "Generated OpenAPI spec for Index meta-database did not match committed version.\nRun 'invoke update-openapijson' and re-commit.\nDiff:\n$index_diff";
exit 1;
fi
