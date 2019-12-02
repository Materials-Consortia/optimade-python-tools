#!/bin/bash
diff=$(jsondiff openapi.json local_openapi.json);
index_diff=$(jsondiff index_openapi.json local_index_openapi.json);

if [ ! "$diff" = "{}" ]; then 
    echo -e "Generated OpenAPI spec for test server did not match committed version.\nRun 'invoke update_openapijson' and re-commit.\nDiff:\n$diff"; 
exit 1;
fi

if [ ! "$index_diff" = "{}" ]; then 
    echo -e "Generated OpenAPI spec for Index meta-database did not match committed version. Diff:\n$index_diff"; 
exit 1;
fi
