#!/bin/bash
diff=$(jsondiff openapi.json local_openapi.json);

if [ ! "$diff" = "{}" ]; then
    echo -e "Generated OpenAPI spec did not match committed version.\nRun 'invoke update_openapijson' and re-commit.\nDiff:\n$diff";
exit 1;
fi
