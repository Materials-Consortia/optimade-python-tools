#!/bin/bash
python -c "from optimade.server.main import app, update_schema; update_schema(app)"
python -c "from optimade.server.main_index import app, update_schema; update_schema(app)"

diff=$(jsondiff ./src/openapi/openapi.json .src/openapi/local_openapi.json);
index_diff=$(jsondiff ./src/openapi/index_openapi.json .src/openapi/local_index_openapi.json);

if [ ! "$diff" = "{}" ]; then
    echo -e "Generated OpenAPI spec for test server did not match committed version.\nRun 'invoke update-openapijson' and re-commit.\nDiff:\n$diff";
exit 1;
fi

if [ ! "$index_diff" = "{}" ]; then
    echo -e "Generated OpenAPI spec for Index meta-database did not match committed version.\nRun 'invoke update-openapijson' and re-commit.\nDiff:\n$index_diff";
exit 1;
fi
