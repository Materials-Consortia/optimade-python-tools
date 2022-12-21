# Changelog

## [Unreleased](https://github.com/Materials-Consortia/optimade-python-tools/tree/HEAD)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.20.2...HEAD)

This release adds the ability to include or exclude particular providers from queries with the `OptimadeClient` class and `optimade-get` CLI, via the provider's registered prefix (#1412)

For example: 

```shell
# Only query databases served by the example providers
optimade-get --include-providers exmpl,optimade
# Exclude example providers from global list
optimade-get --exclude-providers exmpl,optimade
```

You can also now exclude particular databases by their URLs:
```shell
# Exclude specific example databases
optimade-get --exclude-databases https://example.org/optimade,https://optimade.org/example
```

The release also includes some server enhancements and fixes:
- Caching of `/info/` and `/info/<entry>` endpoint responses (#1433)
- A bugfix for the entry mapper classes, which were sharing cache resources globally leading to poor utilization (#1435)

## [v0.20.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.20.2) (2022-12-21)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.20.1...v0.20.2)

This release adds the ability to include or exclude particular providers from queries with the `OptimadeClient` class and `optimade-get` CLI, via the provider's registered prefix (#1412)

For example: 

```shell
# Only query databases served by the example providers
optimade-get --include-providers exmpl,optimade
# Exclude example providers from global list
optimade-get --exclude-providers exmpl,optimade
```

You can also now exclude particular databases by their URLs:
```shell
# Exclude specific example databases
optimade-get --exclude-databases https://example.org/optimade,https://optimade.org/example
```

The release also includes some server enhancements and fixes:
- Caching of `/info/` and `/info/<entry>` endpoint responses (#1433)
- A bugfix for the entry mapper classes, which were sharing cache resources globally leading to poor utilization (#1435)

**Implemented enhancements:**

- Cache `/info` and `/info/<entry>` responses [\#1433](https://github.com/Materials-Consortia/optimade-python-tools/pull/1433) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- `lru_cache`s on the mapper classes are subtly wrong [\#1434](https://github.com/Materials-Consortia/optimade-python-tools/issues/1434)
- Fix for mapper caches [\#1435](https://github.com/Materials-Consortia/optimade-python-tools/pull/1435) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Migrate away from Heroku for demo server [\#1307](https://github.com/Materials-Consortia/optimade-python-tools/issues/1307)
- Add ability to use provider prefixes/custom index base URLs with client [\#1295](https://github.com/Materials-Consortia/optimade-python-tools/issues/1295)

**Merged pull requests:**

- Add pip caches to CI and tidy old flake8 job [\#1442](https://github.com/Materials-Consortia/optimade-python-tools/pull/1442) ([ml-evs](https://github.com/ml-evs))
- Allow empty strings through chemical formula regexp [\#1428](https://github.com/Materials-Consortia/optimade-python-tools/pull/1428) ([ml-evs](https://github.com/ml-evs))
- Explicitly use Python 3.8 environment for pre-commit in CI [\#1421](https://github.com/Materials-Consortia/optimade-python-tools/pull/1421) ([ml-evs](https://github.com/ml-evs))
- Add ability to \(in/ex\)clude providers by ID within client [\#1412](https://github.com/Materials-Consortia/optimade-python-tools/pull/1412) ([ml-evs](https://github.com/ml-evs))

## [v0.20.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.20.1) (2022-12-03)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.20.0...v0.20.1)

**Fixed bugs:**

- Cannot retrieve child database links [\#1410](https://github.com/Materials-Consortia/optimade-python-tools/issues/1410)
- Fix typo that breaks `get_child_databases` retriever [\#1411](https://github.com/Materials-Consortia/optimade-python-tools/pull/1411) ([ml-evs](https://github.com/ml-evs))

## [v0.20.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.20.0) (2022-11-29)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.19.4...v0.20.0)

This release continues the modularisation of the package by moving the server exceptions and warnings out into top-level modules, and removing the core dependency on FastAPI (now a server dependency only). This should allow for easier use of the `optimade.models` and `optimade.client` modules within other packages.

Aside from that, the package now supports Python 3.11, and our example server is now deployed at [Fly.io](https://optimade.fly.dev) rather than Heroku.

**Implemented enhancements:**

- Add support for Python 3.11 [\#1361](https://github.com/Materials-Consortia/optimade-python-tools/issues/1361)
- Improve test diagnostics and fix deprecated Elasticsearch calls [\#1373](https://github.com/Materials-Consortia/optimade-python-tools/pull/1373) ([ml-evs](https://github.com/ml-evs))
- Support Python 3.11 [\#1362](https://github.com/Materials-Consortia/optimade-python-tools/pull/1362) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Elasticsearch pytest oneliner in the docs is no longer working [\#1377](https://github.com/Materials-Consortia/optimade-python-tools/issues/1377)
- Remote swagger validator has changed output format [\#1370](https://github.com/Materials-Consortia/optimade-python-tools/issues/1370)

**Closed issues:**

- Fully isolate server code from other submodules [\#1403](https://github.com/Materials-Consortia/optimade-python-tools/issues/1403)
- OpenAPI schema should not enforce recommended constraint on `page_number` [\#1372](https://github.com/Materials-Consortia/optimade-python-tools/issues/1372)
- Pydantic models docs are broken on the mkdocs site with new renderer [\#1353](https://github.com/Materials-Consortia/optimade-python-tools/issues/1353)
- FastAPI should not be a core dependency [\#1198](https://github.com/Materials-Consortia/optimade-python-tools/issues/1198)

**Merged pull requests:**

- Move exceptions and warnings out of server code and separate deps [\#1405](https://github.com/Materials-Consortia/optimade-python-tools/pull/1405) ([ml-evs](https://github.com/ml-evs))
- Complete migration from Heroku to Fly [\#1400](https://github.com/Materials-Consortia/optimade-python-tools/pull/1400) ([ml-evs](https://github.com/ml-evs))
- Add GH actions for deploying example server to Fly [\#1396](https://github.com/Materials-Consortia/optimade-python-tools/pull/1396) ([ml-evs](https://github.com/ml-evs))
- Support new remote swagger.io validator format [\#1371](https://github.com/Materials-Consortia/optimade-python-tools/pull/1371) ([ml-evs](https://github.com/ml-evs))
- Do not enforce minimum value of `page_number` at model level [\#1369](https://github.com/Materials-Consortia/optimade-python-tools/pull/1369) ([ml-evs](https://github.com/ml-evs))
- Enable `mypy` and `isort` in pre-commit & CI [\#1346](https://github.com/Materials-Consortia/optimade-python-tools/pull/1346) ([ml-evs](https://github.com/ml-evs))
- Remove randomness from structure utils tests [\#1338](https://github.com/Materials-Consortia/optimade-python-tools/pull/1338) ([ml-evs](https://github.com/ml-evs))
- Demote FastAPI to a server dep only [\#1199](https://github.com/Materials-Consortia/optimade-python-tools/pull/1199) ([ml-evs](https://github.com/ml-evs))

## [v0.19.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.19.4) (2022-09-19)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.19.3...v0.19.4)

This is a hotfix release for #1335, a bug regarding chunked responses triggered when using the latest FastAPI version.

**Fixed bugs:**

- UnboundLocalError - `chunk_size` is not always set in middleware method [\#1335](https://github.com/Materials-Consortia/optimade-python-tools/issues/1335)
- Ensure `chunk_size` is properly set when chunking responses [\#1336](https://github.com/Materials-Consortia/optimade-python-tools/pull/1336) ([ml-evs](https://github.com/ml-evs))

## [v0.19.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.19.3) (2022-09-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.19.2...v0.19.3)

**Implemented enhancements:**

- Set correct `meta->schema` value automatically [\#1323](https://github.com/Materials-Consortia/optimade-python-tools/pull/1323) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Pin requirements in CD release workflows [\#1324](https://github.com/Materials-Consortia/optimade-python-tools/pull/1324) ([ml-evs](https://github.com/ml-evs))

## [v0.19.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.19.2) (2022-09-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.19.1...v0.19.2)

**Fixed bugs:**

- Wrong fractional particle positions in test [\#1232](https://github.com/Materials-Consortia/optimade-python-tools/issues/1232)
- Bugfix validator so next links are followed the correct number of times [\#1318](https://github.com/Materials-Consortia/optimade-python-tools/pull/1318) ([JPBergsma](https://github.com/JPBergsma))
- Remove incorrect default value for `page_number` query parameter [\#1303](https://github.com/Materials-Consortia/optimade-python-tools/pull/1303) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- If nperiodic\_dimensions=2 the structure adapter can only properly convert it to ase [\#1212](https://github.com/Materials-Consortia/optimade-python-tools/issues/1212)

**Merged pull requests:**

- Use proper type hint for griffe 0.22 compatibility [\#1313](https://github.com/Materials-Consortia/optimade-python-tools/pull/1313) ([JPBergsma](https://github.com/JPBergsma))
- Adapters now also return lattice information for structures that are periodic in 1 or 2 dimensions. [\#1233](https://github.com/Materials-Consortia/optimade-python-tools/pull/1233) ([JPBergsma](https://github.com/JPBergsma))

## [v0.19.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.19.1) (2022-08-12)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.19.0...v0.19.1)

**Implemented enhancements:**

- Add `from_pymatgen` structure adapter method and concept of ingesters [\#1296](https://github.com/Materials-Consortia/optimade-python-tools/pull/1296) ([ml-evs](https://github.com/ml-evs))
- Add `lru_cache` to many mapper properties [\#1245](https://github.com/Materials-Consortia/optimade-python-tools/pull/1245) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Use animated SVG logo for optimade-python-tools landing page [\#1297](https://github.com/Materials-Consortia/optimade-python-tools/pull/1297) ([ml-evs](https://github.com/ml-evs))

## [v0.19.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.19.0) (2022-07-18)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.18.0...v0.19.0)

This minor release includes several usability improvements for the server and client arising from the OPTIMADE workshop.
This release also drops support for Python 3.7, which should allow us to streamline our dependencies going forward.

**Implemented enhancements:**

- Support for Elasticsearch v7 [\#1216](https://github.com/Materials-Consortia/optimade-python-tools/pull/1216) ([markus1978](https://github.com/markus1978))

**Fixed bugs:**

- Landing page not loading  [\#1256](https://github.com/Materials-Consortia/optimade-python-tools/issues/1256)
- Config values are not cached by `@classproperty` [\#1219](https://github.com/Materials-Consortia/optimade-python-tools/issues/1219)
- Prevent internal validator errors when entries are missing ID/type  [\#1273](https://github.com/Materials-Consortia/optimade-python-tools/pull/1273) ([ml-evs](https://github.com/ml-evs))
- Improve error handling for client when updating provider list [\#1222](https://github.com/Materials-Consortia/optimade-python-tools/pull/1222) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Internal validator failures [\#1272](https://github.com/Materials-Consortia/optimade-python-tools/issues/1272)
- Use versioned Dockerfiles for CI services to allow dependabot to update them [\#1241](https://github.com/Materials-Consortia/optimade-python-tools/issues/1241)
- Wrong links to available endpoints [\#1214](https://github.com/Materials-Consortia/optimade-python-tools/issues/1214)
- The validator should check for `meta->schema` [\#1209](https://github.com/Materials-Consortia/optimade-python-tools/issues/1209)
- Add configurable `meta->schemas` field to reference server [\#1208](https://github.com/Materials-Consortia/optimade-python-tools/issues/1208)

**Merged pull requests:**

- Bump providers from `fb05359` to `a92e5bc` [\#1267](https://github.com/Materials-Consortia/optimade-python-tools/pull/1267) ([dependabot[bot]](https://github.com/apps/dependabot))
- Add schema parameter when calling meta\_values in landing.py [\#1257](https://github.com/Materials-Consortia/optimade-python-tools/pull/1257) ([JPBergsma](https://github.com/JPBergsma))
- Update `lark` dependency to new name [\#1231](https://github.com/Materials-Consortia/optimade-python-tools/pull/1231) ([ml-evs](https://github.com/ml-evs))
- Use Python 3.10 instead of 3.7 in installation instructions [\#1229](https://github.com/Materials-Consortia/optimade-python-tools/pull/1229) ([JPBergsma](https://github.com/JPBergsma))
- Optimisation: do not re-access mapper properties inside the request loop [\#1223](https://github.com/Materials-Consortia/optimade-python-tools/pull/1223) ([ml-evs](https://github.com/ml-evs))
- Add meta-\>schema validation warning [\#1211](https://github.com/Materials-Consortia/optimade-python-tools/pull/1211) ([ml-evs](https://github.com/ml-evs))
- Add configurable `schema_url` and `index_schema_url` options [\#1210](https://github.com/Materials-Consortia/optimade-python-tools/pull/1210) ([ml-evs](https://github.com/ml-evs))
- Drop support for Python 3.7 [\#1179](https://github.com/Materials-Consortia/optimade-python-tools/pull/1179) ([ml-evs](https://github.com/ml-evs))

## [v0.18.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.18.0) (2022-05-29)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.17.2...v0.18.0)

This is a feature release that includes the new `optimade.client.OptimadeClient` class, a client capable asynchronously querying multiple OPTIMADE APIs simultaneously.
It also contains a patch for the OPTIMADE models that allows them to be used with more recent FastAPI versions without breaking OpenAPI 3.0 compatibility.
Other changes can be found below.
This release includes improvements to the validator to catch more cases where OPTIMADE APIs are only partially implemented.
Previously, APIs that did not support filtering, pagination or limiting response fields at all (i.e., the query parameter is simply ignored) would pass most validation tests erroneously in some unlucky situations (#1180).

**Implemented enhancements:**

- The validator should use a custom `User-Agent` header [\#1187](https://github.com/Materials-Consortia/optimade-python-tools/issues/1187)
- Suggestion to include an OPTIMADE python API client [\#932](https://github.com/Materials-Consortia/optimade-python-tools/issues/932)
- Implementation of an OPTIMADE client [\#1154](https://github.com/Materials-Consortia/optimade-python-tools/pull/1154) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- `OptimadeClient` crashes if an index meta-database is down [\#1196](https://github.com/Materials-Consortia/optimade-python-tools/issues/1196)
- Catch connection errors when populating client database list [\#1197](https://github.com/Materials-Consortia/optimade-python-tools/pull/1197) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Add a clearer error message on when trying to use client with missing deps [\#1200](https://github.com/Materials-Consortia/optimade-python-tools/pull/1200) ([ml-evs](https://github.com/ml-evs))
- Use a custom `User-Agent` with validator [\#1189](https://github.com/Materials-Consortia/optimade-python-tools/pull/1189) ([ml-evs](https://github.com/ml-evs))
- Syntactic tweaks to models and schemas for compatibility with `fastapi>0.66` [\#1131](https://github.com/Materials-Consortia/optimade-python-tools/pull/1131) ([ml-evs](https://github.com/ml-evs))

## [v0.17.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.17.2) (2022-05-21)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.17.1...v0.17.2)

This release includes improvements to the validator to catch more cases where OPTIMADE APIs are only partially implemented.
Previously, APIs that did not support filtering, pagination or limiting response fields at all (i.e., the query parameter is simply ignored) would pass most validation tests erroneously in some unlucky situations (#1180).

**Fixed bugs:**

- Server validation incorrectly passes with various unimplemented features [\#1180](https://github.com/Materials-Consortia/optimade-python-tools/issues/1180)

**Merged pull requests:**

- Harden validator for partially implemented APIs [\#1181](https://github.com/Materials-Consortia/optimade-python-tools/pull/1181) ([ml-evs](https://github.com/ml-evs))

## [v0.17.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.17.1) (2022-05-18)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.17.0...v0.17.1)

This patch release adds a pre-built Docker container for the reference server to the GitHub Container Registry (GHCR) and a series of [Deployment instructions](https://www.optimade.org/optimade-python-tools/v0.17.1/deployment/container/) in the online documentation.

The image can be easily pulled from GHCR with:

```docker pull ghcr.io/materials-consortia/optimade```

**Implemented enhancements:**

- Release a container \(Docker\) image for developers [\#1111](https://github.com/Materials-Consortia/optimade-python-tools/issues/1111)

**Closed issues:**

- Issues with GH Changelog updater \(secondary usage API requests\) [\#976](https://github.com/Materials-Consortia/optimade-python-tools/issues/976)

**Merged pull requests:**

- Don't use `env` context for step [\#1178](https://github.com/Materials-Consortia/optimade-python-tools/pull/1178) ([CasperWA](https://github.com/CasperWA))
- Docker image for `optimade` on ghcr.io [\#1171](https://github.com/Materials-Consortia/optimade-python-tools/pull/1171) ([CasperWA](https://github.com/CasperWA))

## [v0.17.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.17.0) (2022-05-10)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.12...v0.17.0)

This minor release contains fixes recommended for those deploying the optimade-python-tools reference server:

- The `meta->data_returned` field was previously incorrect when using the MongoDB backend.
- Incoming URL query parameters are now validated against the provided query parameters class (if using custom query parameters, this class should be extended or the parameters should use your registered provider prefix). This functionality can be disabled with the `validate_query_parameters` config option.
- The results of some queries were not reversible with MongoDB (e.g., `nelements != 2` vs `2 != nelements`); this has now been fixed.

**Implemented enhancements:**

- Add server check for typos in query parameters [\#1120](https://github.com/Materials-Consortia/optimade-python-tools/issues/1120)
- Improve handling of MongoDB ObjectIDs as OPTIMADE `immutable_id` [\#1142](https://github.com/Materials-Consortia/optimade-python-tools/pull/1142) ([ml-evs](https://github.com/ml-evs))
- Add support for number-based pagination  [\#1139](https://github.com/Materials-Consortia/optimade-python-tools/pull/1139) ([JPBergsma](https://github.com/JPBergsma))
- Added option to validate incoming URL query parameters [\#1122](https://github.com/Materials-Consortia/optimade-python-tools/pull/1122) ([JPBergsma](https://github.com/JPBergsma))

**Fixed bugs:**

- `meta->data_returned` is incorrect for paginated results with MongoDB [\#1140](https://github.com/Materials-Consortia/optimade-python-tools/issues/1140)
- Queries with the form: 'value != prop' return entries where 'prop == None'  [\#1133](https://github.com/Materials-Consortia/optimade-python-tools/issues/1133)
- Test on Queries on single structures fail with the check\_response function. [\#1125](https://github.com/Materials-Consortia/optimade-python-tools/issues/1125)
- Fix incorrect `meta->data_returned` for paginated results with MongoDB [\#1141](https://github.com/Materials-Consortia/optimade-python-tools/pull/1141) ([ml-evs](https://github.com/ml-evs))
- Fix cases where comparison first and property first queries did not match [\#1134](https://github.com/Materials-Consortia/optimade-python-tools/pull/1134) ([JPBergsma](https://github.com/JPBergsma))

**Closed issues:**

- Raise error/warning when using unsupported pagination method [\#1132](https://github.com/Materials-Consortia/optimade-python-tools/issues/1132)
- Add missing documentation for serving custom query params and fields [\#1123](https://github.com/Materials-Consortia/optimade-python-tools/issues/1123)

**Merged pull requests:**

- Use GitHub Actions for Heroku deployment [\#1165](https://github.com/Materials-Consortia/optimade-python-tools/pull/1165) ([ml-evs](https://github.com/ml-evs))
- Add docs for custom provider fields and query parameters [\#1164](https://github.com/Materials-Consortia/optimade-python-tools/pull/1164) ([ml-evs](https://github.com/ml-evs))
- Add deprecation warning for Python 3.7 [\#1157](https://github.com/Materials-Consortia/optimade-python-tools/pull/1157) ([ml-evs](https://github.com/ml-evs))
- Added way to specify unsupported query parameters and provide a warning [\#1136](https://github.com/Materials-Consortia/optimade-python-tools/pull/1136) ([ml-evs](https://github.com/ml-evs))
- Adjusted check\_response so it can also handle single entries. [\#1130](https://github.com/Materials-Consortia/optimade-python-tools/pull/1130) ([JPBergsma](https://github.com/JPBergsma))
- Corrected link in Install.MD [\#1124](https://github.com/Materials-Consortia/optimade-python-tools/pull/1124) ([JPBergsma](https://github.com/JPBergsma))

## [v0.16.12](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.12) (2022-03-23)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.11...v0.16.12)

**Implemented enhancements:**

- Make structure adapters infer `species` from `species_at_sites` when missing [\#1103](https://github.com/Materials-Consortia/optimade-python-tools/pull/1103) ([ml-evs](https://github.com/ml-evs))
- Allow specification of provider field descriptions/units etc. in config file [\#1096](https://github.com/Materials-Consortia/optimade-python-tools/pull/1096) ([ml-evs](https://github.com/ml-evs))
- Moving and adding some utilities for client code [\#589](https://github.com/Materials-Consortia/optimade-python-tools/pull/589) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Allow provider field descriptions to be provided in the config [\#1095](https://github.com/Materials-Consortia/optimade-python-tools/issues/1095)

## [v0.16.11](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.11) (2022-03-03)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.10...v0.16.11)

**Merged pull requests:**

- Remove Jinja dependency for landing page generation [\#1082](https://github.com/Materials-Consortia/optimade-python-tools/pull/1082) ([ml-evs](https://github.com/ml-evs))

## [v0.16.10](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.10) (2022-02-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.9...v0.16.10)

**Fixed bugs:**

- Distribution tests failing [\#1061](https://github.com/Materials-Consortia/optimade-python-tools/issues/1061)

**Security fixes:**

- Bump elasticsearch version to avoid CVE-2021-44832 [\#1066](https://github.com/Materials-Consortia/optimade-python-tools/pull/1066) ([JPBergsma](https://github.com/JPBergsma))

**Merged pull requests:**

- Use `build` package to build distributions [\#1062](https://github.com/Materials-Consortia/optimade-python-tools/pull/1062) ([CasperWA](https://github.com/CasperWA))
- Cancel CI PR jobs that are in progress with new changes, add skip\_changelog label to overrides [\#1057](https://github.com/Materials-Consortia/optimade-python-tools/pull/1057) ([ml-evs](https://github.com/ml-evs))
- Prevent validator errors/retries on read timeouts [\#1056](https://github.com/Materials-Consortia/optimade-python-tools/pull/1056) ([ml-evs](https://github.com/ml-evs))

## [v0.16.9](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.9) (2022-01-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.8...v0.16.9)

**Implemented enhancements:**

- Lower validator default read timeout and allow it to be customised [\#1051](https://github.com/Materials-Consortia/optimade-python-tools/pull/1051) ([ml-evs](https://github.com/ml-evs))

**Security fixes:**

- Bump elasticsearch to avoid log4j vulnerability [\#1040](https://github.com/Materials-Consortia/optimade-python-tools/issues/1040)

**Closed issues:**

- Docs reference to `LarkParser` failing. [\#1037](https://github.com/Materials-Consortia/optimade-python-tools/issues/1037)

**Merged pull requests:**

- Update dependabot config and changelog generation [\#1048](https://github.com/Materials-Consortia/optimade-python-tools/pull/1048) ([ml-evs](https://github.com/ml-evs))
- Bump elasticsearch image version to avoid any log4j issues [\#1041](https://github.com/Materials-Consortia/optimade-python-tools/pull/1041) ([ml-evs](https://github.com/ml-evs))
- Make NumPy requirement py version-specific [\#1036](https://github.com/Materials-Consortia/optimade-python-tools/pull/1036) ([CasperWA](https://github.com/CasperWA))

## [v0.16.8](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.8) (2021-12-22)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.7...v0.16.8)

**Implemented enhancements:**

- Support for Python 3.10 [\#956](https://github.com/Materials-Consortia/optimade-python-tools/issues/956)

**Fixed bugs:**

- Overzealous validation of substring comparisons for chemical formula fields [\#1024](https://github.com/Materials-Consortia/optimade-python-tools/issues/1024)

**Merged pull requests:**

- Add configurable field-specific validator overrides to set filter operators as optional [\#1025](https://github.com/Materials-Consortia/optimade-python-tools/pull/1025) ([ml-evs](https://github.com/ml-evs))
- Add Python 3.10 support [\#957](https://github.com/Materials-Consortia/optimade-python-tools/pull/957) ([ml-evs](https://github.com/ml-evs))

## [v0.16.7](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.7) (2021-11-21)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.6...v0.16.7)

**Implemented enhancements:**

- Stricter validation of chemical formulas in OpenAPI schema [\#708](https://github.com/Materials-Consortia/optimade-python-tools/issues/708)

**Fixed bugs:**

- `chemical_formula_anonymous` validator accepts incorrect proportion order if started with 1 [\#1002](https://github.com/Materials-Consortia/optimade-python-tools/issues/1002)

**Closed issues:**

- Versioned docs do not redirect all links correctly [\#977](https://github.com/Materials-Consortia/optimade-python-tools/issues/977)
- Missing support for timestamps/datetime in grammar [\#102](https://github.com/Materials-Consortia/optimade-python-tools/issues/102)

**Merged pull requests:**

- Fixed bug in check\_anonymous\_formula which caused `chemical_formula_anonymous = AB2` to pass validation. [\#1001](https://github.com/Materials-Consortia/optimade-python-tools/pull/1001) ([JPBergsma](https://github.com/JPBergsma))
- Use `diff` for checking PR body [\#1000](https://github.com/Materials-Consortia/optimade-python-tools/pull/1000) ([CasperWA](https://github.com/CasperWA))
- Correct PR body comparison [\#996](https://github.com/Materials-Consortia/optimade-python-tools/pull/996) ([CasperWA](https://github.com/CasperWA))
- Update dependency auto-PR message [\#989](https://github.com/Materials-Consortia/optimade-python-tools/pull/989) ([ml-evs](https://github.com/ml-evs))
- Stricter formula syntax [\#986](https://github.com/Materials-Consortia/optimade-python-tools/pull/986) ([merkys](https://github.com/merkys))
- Implement workflows for dependency updates [\#979](https://github.com/Materials-Consortia/optimade-python-tools/pull/979) ([CasperWA](https://github.com/CasperWA))
- Tidy up old grammars, add a development grammar for v1.2 and update filterparser tests [\#879](https://github.com/Materials-Consortia/optimade-python-tools/pull/879) ([ml-evs](https://github.com/ml-evs))

## [v0.16.6](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.6) (2021-10-19)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.5...v0.16.6)

**Merged pull requests:**

- Put docs release deployment in separate job [\#978](https://github.com/Materials-Consortia/optimade-python-tools/pull/978) ([CasperWA](https://github.com/CasperWA))

## [v0.16.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.5) (2021-10-18)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.4...v0.16.5)

**Closed issues:**

- 'elements\_ratios' model validator uses double-precision machine epsilon - could be relaxed [\#947](https://github.com/Materials-Consortia/optimade-python-tools/issues/947)
- Versioning in Docs [\#724](https://github.com/Materials-Consortia/optimade-python-tools/issues/724)

**Merged pull requests:**

- Fix option value for checkout in CD Docs workflow [\#972](https://github.com/Materials-Consortia/optimade-python-tools/pull/972) ([CasperWA](https://github.com/CasperWA))
- Correct default branch name to `master` [\#971](https://github.com/Materials-Consortia/optimade-python-tools/pull/971) ([CasperWA](https://github.com/CasperWA))
- Automate versioned documentation [\#951](https://github.com/Materials-Consortia/optimade-python-tools/pull/951) ([CasperWA](https://github.com/CasperWA))
- Add JOSS citation [\#949](https://github.com/Materials-Consortia/optimade-python-tools/pull/949) ([ml-evs](https://github.com/ml-evs))
- Some validation QoL tweaks [\#948](https://github.com/Materials-Consortia/optimade-python-tools/pull/948) ([ml-evs](https://github.com/ml-evs))

## [v0.16.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.4) (2021-09-20)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.3...v0.16.4)

**Closed issues:**

- Code check fails because there is no valid version of jsmin [\#938](https://github.com/Materials-Consortia/optimade-python-tools/issues/938)
- Be properly compliant with the new pip resolver [\#625](https://github.com/Materials-Consortia/optimade-python-tools/issues/625)

**Merged pull requests:**

- Bump providers from `357c27b` to `fb05359` [\#945](https://github.com/Materials-Consortia/optimade-python-tools/pull/945) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump providers from `368f9f6` to `357c27b` [\#944](https://github.com/Materials-Consortia/optimade-python-tools/pull/944) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump providers from `91b51bd` to `368f9f6` [\#942](https://github.com/Materials-Consortia/optimade-python-tools/pull/942) ([dependabot[bot]](https://github.com/apps/dependabot))
- remove the dependency on mkdocs-minify because of issue \#938. [\#941](https://github.com/Materials-Consortia/optimade-python-tools/pull/941) ([JPBergsma](https://github.com/JPBergsma))
- Corrected command to call uvicorn server [\#937](https://github.com/Materials-Consortia/optimade-python-tools/pull/937) ([JPBergsma](https://github.com/JPBergsma))
- Use proper pip dependency resolver in publish workflow [\#935](https://github.com/Materials-Consortia/optimade-python-tools/pull/935) ([ml-evs](https://github.com/ml-evs))
- Add JOSS paper [\#804](https://github.com/Materials-Consortia/optimade-python-tools/pull/804) ([ml-evs](https://github.com/ml-evs))

## [v0.16.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.3) (2021-09-02)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.2...v0.16.3)

**Implemented enhancements:**

- Add validation that anonymous/reduced chemical formulae are in fact reduced [\#913](https://github.com/Materials-Consortia/optimade-python-tools/issues/913)

**Fixed bugs:**

- No error/warning when specifying a config file that does not exist [\#930](https://github.com/Materials-Consortia/optimade-python-tools/issues/930)
- Docker tests failing in CI: http://gh\_actions\_host no longer exists? [\#906](https://github.com/Materials-Consortia/optimade-python-tools/issues/906)
- Fix config file warnings when file is missing [\#931](https://github.com/Materials-Consortia/optimade-python-tools/pull/931) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Docs don't introduce the idea of "models" [\#910](https://github.com/Materials-Consortia/optimade-python-tools/issues/910)
- Docs don't mention anything about where to go for support [\#909](https://github.com/Materials-Consortia/optimade-python-tools/issues/909)
- `run.sh` does not appear to be available from the pip installation [\#904](https://github.com/Materials-Consortia/optimade-python-tools/issues/904)
- Missing guide for how to set up an implementation from existing database [\#176](https://github.com/Materials-Consortia/optimade-python-tools/issues/176)

**Merged pull requests:**

- Add tutorial-style guide on setting up an API [\#915](https://github.com/Materials-Consortia/optimade-python-tools/pull/915) ([ml-evs](https://github.com/ml-evs))
- Add validator to check whether anonymous and reduced formulae are reduced [\#914](https://github.com/Materials-Consortia/optimade-python-tools/pull/914) ([ml-evs](https://github.com/ml-evs))
- Clarify the "all models" documentation page [\#912](https://github.com/Materials-Consortia/optimade-python-tools/pull/912) ([ml-evs](https://github.com/ml-evs))
- Add more specific 'Getting Help' info to Contributing and README [\#911](https://github.com/Materials-Consortia/optimade-python-tools/pull/911) ([ml-evs](https://github.com/ml-evs))
- Bump Materials-Consortia/optimade-validator-action from 2.5.0 to 2.6.0 [\#907](https://github.com/Materials-Consortia/optimade-python-tools/pull/907) ([dependabot[bot]](https://github.com/apps/dependabot))
- Clarify installation methods by use-case [\#905](https://github.com/Materials-Consortia/optimade-python-tools/pull/905) ([ml-evs](https://github.com/ml-evs))
- Relax response top-level root validator [\#903](https://github.com/Materials-Consortia/optimade-python-tools/pull/903) ([CasperWA](https://github.com/CasperWA))
- Add integrated app docs, tweak other use case docs [\#883](https://github.com/Materials-Consortia/optimade-python-tools/pull/883) ([ml-evs](https://github.com/ml-evs))

## [v0.16.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.2) (2021-08-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.1...v0.16.2)

**Fixed bugs:**

- Provider fallbacks are still not working [\#896](https://github.com/Materials-Consortia/optimade-python-tools/issues/896)
- Fix provider fallbacks [\#897](https://github.com/Materials-Consortia/optimade-python-tools/pull/897) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Dependency updates for v0.16.2 [\#894](https://github.com/Materials-Consortia/optimade-python-tools/pull/894) ([ml-evs](https://github.com/ml-evs))
- Bump codecov/codecov-action from 2.0.1 to 2.0.2 [\#882](https://github.com/Materials-Consortia/optimade-python-tools/pull/882) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump codecov/codecov-action from 1.5.2 to 2.0.1 [\#878](https://github.com/Materials-Consortia/optimade-python-tools/pull/878) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.16.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.1) (2021-07-15)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.16.0...v0.16.1)

**Implemented enhancements:**

- Change MIME type to application/vnd.api+json where appropriate [\#875](https://github.com/Materials-Consortia/optimade-python-tools/issues/875)
- Minor corrections + use model aliases for `handle_response_fields()` [\#876](https://github.com/Materials-Consortia/optimade-python-tools/pull/876) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Wrong behaviour HAS ONLY query for MongoDB [\#810](https://github.com/Materials-Consortia/optimade-python-tools/issues/810)
- Correct the behaviour of HAS ONLY with MongoDB backend [\#861](https://github.com/Materials-Consortia/optimade-python-tools/pull/861) ([JPBergsma](https://github.com/JPBergsma))

**Merged pull requests:**

- Change default MIME type to "application/vnd.api+json" [\#877](https://github.com/Materials-Consortia/optimade-python-tools/pull/877) ([ml-evs](https://github.com/ml-evs))
- Update elements description to match specification [\#874](https://github.com/Materials-Consortia/optimade-python-tools/pull/874) ([ml-evs](https://github.com/ml-evs))

## [v0.16.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.16.0) (2021-07-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.5...v0.16.0)

**Closed issues:**

- Incoming model update \(new field: issue\_tracker\) [\#592](https://github.com/Materials-Consortia/optimade-python-tools/issues/592)

**Merged pull requests:**

- Add issue\_tracker field to provider model [\#593](https://github.com/Materials-Consortia/optimade-python-tools/pull/593) ([ml-evs](https://github.com/ml-evs))

## [v0.15.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.5) (2021-07-04)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.4...v0.15.5)

**Fixed bugs:**

- NOT filter operation of mongo query for complex expressions [\#79](https://github.com/Materials-Consortia/optimade-python-tools/issues/79)

**Closed issues:**

- Remove CI psycopg2-binary install when aiida-core\>1.6.3 [\#855](https://github.com/Materials-Consortia/optimade-python-tools/issues/855)
- Pytest fails at Setup environment for AiiDA [\#853](https://github.com/Materials-Consortia/optimade-python-tools/issues/853)
- Add timeout parameter to validator [\#681](https://github.com/Materials-Consortia/optimade-python-tools/issues/681)
- Add note in installation instructions about pulling submodule for providers [\#370](https://github.com/Materials-Consortia/optimade-python-tools/issues/370)

**Merged pull requests:**

- Add request --timeout parameter to validator [\#860](https://github.com/Materials-Consortia/optimade-python-tools/pull/860) ([ml-evs](https://github.com/ml-evs))
- Bump providers from `fa25ed3` to `91b51bd` [\#858](https://github.com/Materials-Consortia/optimade-python-tools/pull/858) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update to AiiDA v1.6.4 and remove CI fix [\#857](https://github.com/Materials-Consortia/optimade-python-tools/pull/857) ([CasperWA](https://github.com/CasperWA))
- Temporary fix for CI tests with AiiDA [\#854](https://github.com/Materials-Consortia/optimade-python-tools/pull/854) ([CasperWA](https://github.com/CasperWA))
- Documentation tweaks [\#852](https://github.com/Materials-Consortia/optimade-python-tools/pull/852) ([JPBergsma](https://github.com/JPBergsma))
- Fix query negation in MongoDB [\#814](https://github.com/Materials-Consortia/optimade-python-tools/pull/814) ([JPBergsma](https://github.com/JPBergsma))

## [v0.15.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.4) (2021-06-15)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.3...v0.15.4)

**Implemented enhancements:**

- Missing documentation for new configuration methods [\#766](https://github.com/Materials-Consortia/optimade-python-tools/issues/766)

**Closed issues:**

- Add docs "use case" for the validator [\#841](https://github.com/Materials-Consortia/optimade-python-tools/issues/841)
- Use specific configuration file for Heroku deployment [\#738](https://github.com/Materials-Consortia/optimade-python-tools/issues/738)
- Potential submission to JOSS? [\#203](https://github.com/Materials-Consortia/optimade-python-tools/issues/203)
- Add more tests [\#104](https://github.com/Materials-Consortia/optimade-python-tools/issues/104)

**Merged pull requests:**

- Tweak configuration docs [\#851](https://github.com/Materials-Consortia/optimade-python-tools/pull/851) ([ml-evs](https://github.com/ml-evs))
- Add some more tutorial-style documentation [\#850](https://github.com/Materials-Consortia/optimade-python-tools/pull/850) ([ml-evs](https://github.com/ml-evs))

## [v0.15.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.3) (2021-06-10)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.2...v0.15.3)

**Merged pull requests:**

- Update model descriptions following spec updates [\#847](https://github.com/Materials-Consortia/optimade-python-tools/pull/847) ([ml-evs](https://github.com/ml-evs))

## [v0.15.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.2) (2021-06-10)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.1...v0.15.2)

**Implemented enhancements:**

- Missing HTTP response codes in OpenAPI schema [\#763](https://github.com/Materials-Consortia/optimade-python-tools/issues/763)

**Merged pull requests:**

- Update response model information for routes [\#846](https://github.com/Materials-Consortia/optimade-python-tools/pull/846) ([CasperWA](https://github.com/CasperWA))
- Improve semver validation error messsage [\#845](https://github.com/Materials-Consortia/optimade-python-tools/pull/845) ([ml-evs](https://github.com/ml-evs))
- Bump codecov/codecov-action from 1.5.0 to 1.5.2 [\#843](https://github.com/Materials-Consortia/optimade-python-tools/pull/843) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.15.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.1) (2021-06-08)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.15.0...v0.15.1)

**Closed issues:**

- mongomock $size queries match all non-array fields for {$size: 1}, even nulls [\#807](https://github.com/Materials-Consortia/optimade-python-tools/issues/807)
- Allow custom headers to be specified for validation [\#790](https://github.com/Materials-Consortia/optimade-python-tools/issues/790)

**Merged pull requests:**

- Add --headers argument to validator to allow passing e.g. API keys [\#806](https://github.com/Materials-Consortia/optimade-python-tools/pull/806) ([ml-evs](https://github.com/ml-evs))

## [v0.15.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.15.0) (2021-06-01)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.14.1...v0.15.0)

**Fixed bugs:**

- Provider fallbacks do not get used [\#829](https://github.com/Materials-Consortia/optimade-python-tools/issues/829)
- ParserError's should not return 500 HTTP status codes [\#812](https://github.com/Materials-Consortia/optimade-python-tools/issues/812)
- Fix provider fallback list [\#830](https://github.com/Materials-Consortia/optimade-python-tools/pull/830) ([ml-evs](https://github.com/ml-evs))
- Return 400 Bad Request \(not 500\) on filter parser errors, plus filterparser module facelift [\#813](https://github.com/Materials-Consortia/optimade-python-tools/pull/813) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Move aliasing code to base transformer [\#743](https://github.com/Materials-Consortia/optimade-python-tools/issues/743)
- Missing optional fields are not returned as null when requested with response\_fields [\#516](https://github.com/Materials-Consortia/optimade-python-tools/issues/516)

**Merged pull requests:**

- Update INSTALL docs [\#811](https://github.com/Materials-Consortia/optimade-python-tools/pull/811) ([ml-evs](https://github.com/ml-evs))
- Overhaul of filter transformers, mappers and response fields [\#797](https://github.com/Materials-Consortia/optimade-python-tools/pull/797) ([ml-evs](https://github.com/ml-evs))

## [v0.14.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.14.1) (2021-05-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.14.0...v0.14.1)

**Fixed bugs:**

- \[SECURITY\] Cycle secrets [\#777](https://github.com/Materials-Consortia/optimade-python-tools/issues/777)

**Closed issues:**

- Do not validate extension endpoints [\#793](https://github.com/Materials-Consortia/optimade-python-tools/issues/793)
- Verify that missing values are not returned in comparisons [\#792](https://github.com/Materials-Consortia/optimade-python-tools/issues/792)

**Merged pull requests:**

- Update GH actions [\#803](https://github.com/Materials-Consortia/optimade-python-tools/pull/803) ([CasperWA](https://github.com/CasperWA))
- Handling null fields in the filtertransformer and validator [\#796](https://github.com/Materials-Consortia/optimade-python-tools/pull/796) ([ml-evs](https://github.com/ml-evs))
- Filter out extension endpoints before validation [\#794](https://github.com/Materials-Consortia/optimade-python-tools/pull/794) ([ml-evs](https://github.com/ml-evs))
- Bump providers from `7a54843` to `fa25ed3` [\#791](https://github.com/Materials-Consortia/optimade-python-tools/pull/791) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump CharMixer/auto-changelog-action from v1.2 to v1.3 [\#778](https://github.com/Materials-Consortia/optimade-python-tools/pull/778) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.14.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.14.0) (2021-03-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.3...v0.14.0)

**Implemented enhancements:**

- Rename config variable use\_real\_mongo to something more general [\#742](https://github.com/Materials-Consortia/optimade-python-tools/issues/742)
- Custom configuration extensions & use standard pydantic way of loading config file [\#739](https://github.com/Materials-Consortia/optimade-python-tools/issues/739)
- Generalising collections and adding ElasticsearchCollection [\#660](https://github.com/Materials-Consortia/optimade-python-tools/pull/660) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Over-aggressive middleware to check versioned base URL [\#737](https://github.com/Materials-Consortia/optimade-python-tools/issues/737)
- Floating point comparisons should not be tested with the validator [\#735](https://github.com/Materials-Consortia/optimade-python-tools/issues/735)
- Mapper method `alias_of` extracts alias wrongly [\#667](https://github.com/Materials-Consortia/optimade-python-tools/issues/667)

**Closed issues:**

- Docs builds are not properly tested for each PR [\#747](https://github.com/Materials-Consortia/optimade-python-tools/issues/747)

**Merged pull requests:**

- Fix CheckWronglyVersionedBaseUrls middleware \(for landing pages\) [\#752](https://github.com/Materials-Consortia/optimade-python-tools/pull/752) ([CasperWA](https://github.com/CasperWA))
- Deprecate Python 3.6 support, v0.14 last supported version [\#751](https://github.com/Materials-Consortia/optimade-python-tools/pull/751) ([CasperWA](https://github.com/CasperWA))
- Run full API docs invoke task for every PR [\#748](https://github.com/Materials-Consortia/optimade-python-tools/pull/748) ([ml-evs](https://github.com/ml-evs))
- Change aliasing method names in mapper and deprecate the old [\#746](https://github.com/Materials-Consortia/optimade-python-tools/pull/746) ([ml-evs](https://github.com/ml-evs))
- Bump providers from `e2074e8` to `7a54843` [\#741](https://github.com/Materials-Consortia/optimade-python-tools/pull/741) ([dependabot[bot]](https://github.com/apps/dependabot))
- Config updates [\#740](https://github.com/Materials-Consortia/optimade-python-tools/pull/740) ([CasperWA](https://github.com/CasperWA))
- Disable all floating-point comparisons during validation [\#736](https://github.com/Materials-Consortia/optimade-python-tools/pull/736) ([ml-evs](https://github.com/ml-evs))
- Report user errors in filter as HTTP 400 Bad Request and not 501 Not Implemented [\#658](https://github.com/Materials-Consortia/optimade-python-tools/pull/658) ([markus1978](https://github.com/markus1978))

## [v0.13.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.3) (2021-03-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.2...v0.13.3)

**Fixed bugs:**

- Python 3.9 support invalid [\#728](https://github.com/Materials-Consortia/optimade-python-tools/issues/728)

**Merged pull requests:**

- Update pydantic to ~=1.8 [\#731](https://github.com/Materials-Consortia/optimade-python-tools/pull/731) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `da74513` to `e2074e8` [\#727](https://github.com/Materials-Consortia/optimade-python-tools/pull/727) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.13.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.2) (2021-03-01)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.1...v0.13.2)

**Implemented enhancements:**

- Improve validation of providers [\#723](https://github.com/Materials-Consortia/optimade-python-tools/issues/723)

## [v0.13.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.1) (2021-02-23)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.13.0...v0.13.1)

**Fixed bugs:**

- Supported OPTIMADE \_\_api\_version\_\_ is incorrect in latest release [\#712](https://github.com/Materials-Consortia/optimade-python-tools/issues/712)

**Merged pull requests:**

- Bump OPTIMADE version [\#713](https://github.com/Materials-Consortia/optimade-python-tools/pull/713) ([ml-evs](https://github.com/ml-evs))

## [v0.13.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.13.0) (2021-02-20)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.9...v0.13.0)

**Closed issues:**

- Update species.mass model [\#630](https://github.com/Materials-Consortia/optimade-python-tools/issues/630)

**Merged pull requests:**

- Update species-\>mass field following specification change [\#631](https://github.com/Materials-Consortia/optimade-python-tools/pull/631) ([ml-evs](https://github.com/ml-evs))

## [v0.12.9](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.9) (2021-02-10)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.8...v0.12.9)

**Implemented enhancements:**

- Improve support for timestamp queries in MongoTransformer [\#590](https://github.com/Materials-Consortia/optimade-python-tools/pull/590) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Use Enums for pydantic model defaults instead of strings [\#683](https://github.com/Materials-Consortia/optimade-python-tools/issues/683)

**Closed issues:**

- When using `--as-type` in validator, one does not get a summary \(`--json` doesn't work\) [\#699](https://github.com/Materials-Consortia/optimade-python-tools/issues/699)
- Extension/import issue with mongo collection [\#682](https://github.com/Materials-Consortia/optimade-python-tools/issues/682)

**Merged pull requests:**

- Always print summary as last thing in validation [\#700](https://github.com/Materials-Consortia/optimade-python-tools/pull/700) ([CasperWA](https://github.com/CasperWA))
- Fixes for new gateway implementation [\#684](https://github.com/Materials-Consortia/optimade-python-tools/pull/684) ([CasperWA](https://github.com/CasperWA))

## [v0.12.8](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.8) (2021-01-18)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.7...v0.12.8)

**Implemented enhancements:**

- Validate mandatory query field `structure_features` [\#678](https://github.com/Materials-Consortia/optimade-python-tools/issues/678)

**Fixed bugs:**

- Validator should not rely on `meta->data_available` [\#677](https://github.com/Materials-Consortia/optimade-python-tools/issues/677)
- Validator should not rely on SHOULD "meta" field "data\_returned" [\#675](https://github.com/Materials-Consortia/optimade-python-tools/issues/675)
- Validator: remove reliance on meta fields and check mandatory queries [\#676](https://github.com/Materials-Consortia/optimade-python-tools/pull/676) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Bump providers from `542ac0a` to `da74513` [\#679](https://github.com/Materials-Consortia/optimade-python-tools/pull/679) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.12.7](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.7) (2021-01-15)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.6...v0.12.7)

**Implemented enhancements:**

- Make content-type response checks on '/versions` endpoint optional [\#670](https://github.com/Materials-Consortia/optimade-python-tools/pull/670) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Publish workflow fails when no changes to api docs between versions [\#673](https://github.com/Materials-Consortia/optimade-python-tools/issues/673)
- /versions header `Content-Type` value should be granularized according to RFC requirements in validator [\#669](https://github.com/Materials-Consortia/optimade-python-tools/issues/669)
- Misleading error message from validator on failure from '/versions' [\#668](https://github.com/Materials-Consortia/optimade-python-tools/issues/668)
- Fix publishing workflow [\#674](https://github.com/Materials-Consortia/optimade-python-tools/pull/674) ([ml-evs](https://github.com/ml-evs))

**Merged pull requests:**

- Update codecov coverage config file [\#672](https://github.com/Materials-Consortia/optimade-python-tools/pull/672) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `fe5048b` to `542ac0a` [\#671](https://github.com/Materials-Consortia/optimade-python-tools/pull/671) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.12.6](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.6) (2021-01-08)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.5...v0.12.6)

**Implemented enhancements:**

- Create base transformer [\#286](https://github.com/Materials-Consortia/optimade-python-tools/issues/286)

**Fixed bugs:**

- Our models and validator are too strict [\#399](https://github.com/Materials-Consortia/optimade-python-tools/issues/399)
- Validator changes: always check unversioned '/versions' and handle rich HTML pages [\#665](https://github.com/Materials-Consortia/optimade-python-tools/pull/665) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Add more prominent link to rendered docs [\#628](https://github.com/Materials-Consortia/optimade-python-tools/issues/628)
- Review the required properties of StructureResourceAttributes in openapi.json [\#198](https://github.com/Materials-Consortia/optimade-python-tools/issues/198)

**Merged pull requests:**

- Added GitHub CODEOWNERS [\#664](https://github.com/Materials-Consortia/optimade-python-tools/pull/664) ([ml-evs](https://github.com/ml-evs))
- Robustness improvements to validator [\#659](https://github.com/Materials-Consortia/optimade-python-tools/pull/659) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#655](https://github.com/Materials-Consortia/optimade-python-tools/pull/655) ([CasperWA](https://github.com/CasperWA))
- Bugfixes for elasticsearch filtertransformer comparision operators. [\#648](https://github.com/Materials-Consortia/optimade-python-tools/pull/648) ([markus1978](https://github.com/markus1978))
- Added "root\_path" config parameter for FastAPI apps [\#634](https://github.com/Materials-Consortia/optimade-python-tools/pull/634) ([markus1978](https://github.com/markus1978))
- Bump providers from `2673be6` to `fe5048b` [\#633](https://github.com/Materials-Consortia/optimade-python-tools/pull/633) ([dependabot[bot]](https://github.com/apps/dependabot))
- Updated README and moved some files to top-level [\#629](https://github.com/Materials-Consortia/optimade-python-tools/pull/629) ([ml-evs](https://github.com/ml-evs))
- insert reading of default optimade\_config.json in example run script run.sh [\#627](https://github.com/Materials-Consortia/optimade-python-tools/pull/627) ([rartino](https://github.com/rartino))
- Create template filtertransformer BaseTransformer [\#287](https://github.com/Materials-Consortia/optimade-python-tools/pull/287) ([ml-evs](https://github.com/ml-evs))

## [v0.12.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.5) (2020-12-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.4...v0.12.5)

**Closed issues:**

- PyPI publishing build is broken by latest pip [\#624](https://github.com/Materials-Consortia/optimade-python-tools/issues/624)
- Empty endpoints raise errors on validation [\#622](https://github.com/Materials-Consortia/optimade-python-tools/issues/622)
- Frequency of updating online docs [\#452](https://github.com/Materials-Consortia/optimade-python-tools/issues/452)

**Merged pull requests:**

- Fix PyPI publishing in CI [\#623](https://github.com/Materials-Consortia/optimade-python-tools/pull/623) ([ml-evs](https://github.com/ml-evs))
- Change validation error to warning on empty endpoints [\#621](https://github.com/Materials-Consortia/optimade-python-tools/pull/621) ([ml-evs](https://github.com/ml-evs))
- Update dependencies [\#620](https://github.com/Materials-Consortia/optimade-python-tools/pull/620) ([CasperWA](https://github.com/CasperWA))
- Upstream fixes from specification [\#611](https://github.com/Materials-Consortia/optimade-python-tools/pull/611) ([ml-evs](https://github.com/ml-evs))
- Minor fixes for the validator [\#610](https://github.com/Materials-Consortia/optimade-python-tools/pull/610) ([ml-evs](https://github.com/ml-evs))
- include LICENSE in pip Package [\#594](https://github.com/Materials-Consortia/optimade-python-tools/pull/594) ([jan-janssen](https://github.com/jan-janssen))
- Relax models to allow for all SHOULD fields to be None [\#560](https://github.com/Materials-Consortia/optimade-python-tools/pull/560) ([ml-evs](https://github.com/ml-evs))
- Python 3.9 support [\#558](https://github.com/Materials-Consortia/optimade-python-tools/pull/558) ([ml-evs](https://github.com/ml-evs))
- ReadTheDocs configuration file \(v2\) [\#485](https://github.com/Materials-Consortia/optimade-python-tools/pull/485) ([CasperWA](https://github.com/CasperWA))

## [v0.12.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.4) (2020-11-16)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.3...v0.12.4)

**Merged pull requests:**

- Minor fixes for versions endpoint validation [\#591](https://github.com/Materials-Consortia/optimade-python-tools/pull/591) ([ml-evs](https://github.com/ml-evs))
- Add --minimal/--page\_limit validator options and remove old code [\#571](https://github.com/Materials-Consortia/optimade-python-tools/pull/571) ([ml-evs](https://github.com/ml-evs))

## [v0.12.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.3) (2020-11-04)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.2...v0.12.3)

**Fixed bugs:**

- GITHUB\_TOKEN not useful for changelog action [\#587](https://github.com/Materials-Consortia/optimade-python-tools/issues/587)
- Hill notation wrong \(still\) [\#585](https://github.com/Materials-Consortia/optimade-python-tools/issues/585)
- Hill notation validation turning around C and H [\#581](https://github.com/Materials-Consortia/optimade-python-tools/issues/581)

**Closed issues:**

- Make structure "deformity" tests more robust [\#583](https://github.com/Materials-Consortia/optimade-python-tools/issues/583)
- Incomplete output of optimade-validator [\#568](https://github.com/Materials-Consortia/optimade-python-tools/issues/568)

**Merged pull requests:**

- Use special release PAT for CHANGELOG generation action [\#588](https://github.com/Materials-Consortia/optimade-python-tools/pull/588) ([CasperWA](https://github.com/CasperWA))
- Check for carbon in elements for Hill [\#586](https://github.com/Materials-Consortia/optimade-python-tools/pull/586) ([CasperWA](https://github.com/CasperWA))
- Added better expected error messages to deformity tests [\#584](https://github.com/Materials-Consortia/optimade-python-tools/pull/584) ([ml-evs](https://github.com/ml-evs))
- Fix Hill ordering validation [\#582](https://github.com/Materials-Consortia/optimade-python-tools/pull/582) ([CasperWA](https://github.com/CasperWA))
- Moved CONFIG import so it does not get triggered when just importing mapper [\#569](https://github.com/Materials-Consortia/optimade-python-tools/pull/569) ([ml-evs](https://github.com/ml-evs))

## [v0.12.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.2) (2020-10-31)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.1...v0.12.2)

**Implemented enhancements:**

- Add convenience method for adding all required middleware [\#536](https://github.com/Materials-Consortia/optimade-python-tools/issues/536)
- Add model validators and regexp for chemical formulae fields [\#547](https://github.com/Materials-Consortia/optimade-python-tools/pull/547) ([ml-evs](https://github.com/ml-evs))
- Validator improvements [\#515](https://github.com/Materials-Consortia/optimade-python-tools/pull/515) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- 'Chosen entry had no value for ...' when property is not requested [\#514](https://github.com/Materials-Consortia/optimade-python-tools/issues/514)
- Fix Species validators and error messages [\#561](https://github.com/Materials-Consortia/optimade-python-tools/pull/561) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Chemical symbols D and T [\#570](https://github.com/Materials-Consortia/optimade-python-tools/issues/570)
- Spurious validation errors in Structure-\>Species [\#559](https://github.com/Materials-Consortia/optimade-python-tools/issues/559)
- Chemical formulae are not properly validated on model creation [\#546](https://github.com/Materials-Consortia/optimade-python-tools/issues/546)

**Merged pull requests:**

- Bump CasperWA/push-protected from v1 to v2.1.0 [\#573](https://github.com/Materials-Consortia/optimade-python-tools/pull/573) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update deps [\#566](https://github.com/Materials-Consortia/optimade-python-tools/pull/566) ([ml-evs](https://github.com/ml-evs))
- Improve handling of MongoDB ObjectID [\#557](https://github.com/Materials-Consortia/optimade-python-tools/pull/557) ([ml-evs](https://github.com/ml-evs))
- Updated dependencies [\#551](https://github.com/Materials-Consortia/optimade-python-tools/pull/551) ([ml-evs](https://github.com/ml-evs))
- Update dependencies - remove black as direct dependency [\#545](https://github.com/Materials-Consortia/optimade-python-tools/pull/545) ([CasperWA](https://github.com/CasperWA))
- Added convenience variables for middleware and exception handlers [\#537](https://github.com/Materials-Consortia/optimade-python-tools/pull/537) ([ml-evs](https://github.com/ml-evs))

## [v0.12.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.1) (2020-09-24)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.12.0...v0.12.1)

**Implemented enhancements:**

- Move entry schemas to separate submodule [\#511](https://github.com/Materials-Consortia/optimade-python-tools/pull/511) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator should allow implementations to return "501 Not Implemented" for unsupported filters [\#518](https://github.com/Materials-Consortia/optimade-python-tools/issues/518)
- Landing page wrong URL  [\#371](https://github.com/Materials-Consortia/optimade-python-tools/issues/371)

**Merged pull requests:**

- This should ensure requirements\*.txt are tested [\#527](https://github.com/Materials-Consortia/optimade-python-tools/pull/527) ([CasperWA](https://github.com/CasperWA))
- Update dependencies [\#526](https://github.com/Materials-Consortia/optimade-python-tools/pull/526) ([CasperWA](https://github.com/CasperWA))
- Fix landing page URL [\#519](https://github.com/Materials-Consortia/optimade-python-tools/pull/519) ([shyamd](https://github.com/shyamd))
- Fixing typo `validatated` -\> `validated` [\#506](https://github.com/Materials-Consortia/optimade-python-tools/pull/506) ([merkys](https://github.com/merkys))
- Make validator respond to KeyboardInterrupts [\#505](https://github.com/Materials-Consortia/optimade-python-tools/pull/505) ([ml-evs](https://github.com/ml-evs))
- Add support levels to validator config [\#503](https://github.com/Materials-Consortia/optimade-python-tools/pull/503) ([ml-evs](https://github.com/ml-evs))
- Enable JSON response from the validator [\#502](https://github.com/Materials-Consortia/optimade-python-tools/pull/502) ([ml-evs](https://github.com/ml-evs))

## [v0.12.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.12.0) (2020-09-11)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.11.0...v0.12.0)

**Fixed bugs:**

- Missing field descriptions in schema for Species-\>name and Person-\>name [\#492](https://github.com/Materials-Consortia/optimade-python-tools/issues/492)
- "type" field not marked as required for derived entry resource models [\#479](https://github.com/Materials-Consortia/optimade-python-tools/issues/479)
- OpenAPI validations fails due to incorrect type of "dimension\_types" [\#478](https://github.com/Materials-Consortia/optimade-python-tools/issues/478)
- Have fallbacks for retrieving providers list [\#450](https://github.com/Materials-Consortia/optimade-python-tools/issues/450)
- Commit only when necessary [\#495](https://github.com/Materials-Consortia/optimade-python-tools/pull/495) ([CasperWA](https://github.com/CasperWA))
- Fix field optonality inconsistency in schema [\#482](https://github.com/Materials-Consortia/optimade-python-tools/pull/482) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator message for wrong version [\#493](https://github.com/Materials-Consortia/optimade-python-tools/issues/493)
- Validator should validate versions endpoint [\#491](https://github.com/Materials-Consortia/optimade-python-tools/issues/491)
- List of providers not included in `/links` endpoint for index meta-database [\#454](https://github.com/Materials-Consortia/optimade-python-tools/issues/454)
- Validate bad version URLs responding with 553 Version Not Supported [\#427](https://github.com/Materials-Consortia/optimade-python-tools/issues/427)
- Nonexistent property 'list' in validator tests [\#423](https://github.com/Materials-Consortia/optimade-python-tools/issues/423)
- Test `data_returned` [\#402](https://github.com/Materials-Consortia/optimade-python-tools/issues/402)
- AiiDA tests only run on Python 3.8 in CI [\#401](https://github.com/Materials-Consortia/optimade-python-tools/issues/401)
- Links under top-level 'links' may be objects [\#394](https://github.com/Materials-Consortia/optimade-python-tools/issues/394)
- Suggestion: use absolute imports in app code to allow re-use [\#298](https://github.com/Materials-Consortia/optimade-python-tools/issues/298)
- error when browsing OpenAPI docs [\#192](https://github.com/Materials-Consortia/optimade-python-tools/issues/192)

**Merged pull requests:**

- Don't report untracked and ignored files [\#496](https://github.com/Materials-Consortia/optimade-python-tools/pull/496) ([CasperWA](https://github.com/CasperWA))
- Improved error message for bad version returning 553 [\#494](https://github.com/Materials-Consortia/optimade-python-tools/pull/494) ([ml-evs](https://github.com/ml-evs))
- Allow Link objects for pagination [\#484](https://github.com/Materials-Consortia/optimade-python-tools/pull/484) ([ml-evs](https://github.com/ml-evs))
- Absolute imports [\#483](https://github.com/Materials-Consortia/optimade-python-tools/pull/483) ([CasperWA](https://github.com/CasperWA))
- Validate OpenAPI specification in CI [\#481](https://github.com/Materials-Consortia/optimade-python-tools/pull/481) ([ml-evs](https://github.com/ml-evs))
- Update types to align with OpenAPI [\#480](https://github.com/Materials-Consortia/optimade-python-tools/pull/480) ([CasperWA](https://github.com/CasperWA))
- Unpin CI Python version for AiiDA tests [\#472](https://github.com/Materials-Consortia/optimade-python-tools/pull/472) ([ml-evs](https://github.com/ml-evs))
- Provider list fallback and list of providers in both servers' `/links`-endpoints [\#455](https://github.com/Materials-Consortia/optimade-python-tools/pull/455) ([CasperWA](https://github.com/CasperWA))
- SHOULD/MUST/OPTIONAL fields in models [\#453](https://github.com/Materials-Consortia/optimade-python-tools/pull/453) ([ml-evs](https://github.com/ml-evs))
- Validator overhaul [\#417](https://github.com/Materials-Consortia/optimade-python-tools/pull/417) ([ml-evs](https://github.com/ml-evs))

## [v0.11.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.11.0) (2020-08-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.10.0...v0.11.0)

**Implemented enhancements:**

- Use logging more thoroughly throughout the code base [\#242](https://github.com/Materials-Consortia/optimade-python-tools/issues/242)
- Implement `warnings` [\#105](https://github.com/Materials-Consortia/optimade-python-tools/issues/105)

**Fixed bugs:**

- Heroku is failing - raising OSError when making LOGS\_DIR [\#448](https://github.com/Materials-Consortia/optimade-python-tools/issues/448)
- `/versions` endpoint content-type parameter "header=present" is provided in the wrong place [\#418](https://github.com/Materials-Consortia/optimade-python-tools/issues/418)
- Publish workflow cannot push to protected branch [\#341](https://github.com/Materials-Consortia/optimade-python-tools/issues/341)
- Fix circular dep and extra permission error in logs [\#436](https://github.com/Materials-Consortia/optimade-python-tools/pull/436) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- log\_dir option in config is unused [\#435](https://github.com/Materials-Consortia/optimade-python-tools/issues/435)
- Allow all types of JSON API relationships [\#429](https://github.com/Materials-Consortia/optimade-python-tools/issues/429)
- OPTIMADE version badge was not bumped on 1.0 release [\#415](https://github.com/Materials-Consortia/optimade-python-tools/issues/415)
- Add `api_hint` query parameter [\#392](https://github.com/Materials-Consortia/optimade-python-tools/issues/392)
- Return 553 for wrongly versioned base URLs [\#391](https://github.com/Materials-Consortia/optimade-python-tools/issues/391)
- Private/dunder methods incorrectly documented in mkdocs [\#365](https://github.com/Materials-Consortia/optimade-python-tools/issues/365)
- Configuration documentation [\#310](https://github.com/Materials-Consortia/optimade-python-tools/issues/310)
- Improve handling of sorting in MongoDB backend [\#276](https://github.com/Materials-Consortia/optimade-python-tools/issues/276)

**Merged pull requests:**

- Catch OSError instead of PermissionError when making log dir [\#449](https://github.com/Materials-Consortia/optimade-python-tools/pull/449) ([CasperWA](https://github.com/CasperWA))
- Introduce logging [\#432](https://github.com/Materials-Consortia/optimade-python-tools/pull/432) ([CasperWA](https://github.com/CasperWA))
- New middleware to catch any `OptimadeWarning`s [\#431](https://github.com/Materials-Consortia/optimade-python-tools/pull/431) ([CasperWA](https://github.com/CasperWA))
- Auto-generate API reference in docs and an overhaul [\#430](https://github.com/Materials-Consortia/optimade-python-tools/pull/430) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `52027b1` to `9712dd8` [\#428](https://github.com/Materials-Consortia/optimade-python-tools/pull/428) ([dependabot[bot]](https://github.com/apps/dependabot))
- Cleanup config files [\#426](https://github.com/Materials-Consortia/optimade-python-tools/pull/426) ([CasperWA](https://github.com/CasperWA))
- Update more unittest tests to pytest [\#425](https://github.com/Materials-Consortia/optimade-python-tools/pull/425) ([CasperWA](https://github.com/CasperWA))
- Sorting on unknown properties: returning Bad Request when appropriate [\#424](https://github.com/Materials-Consortia/optimade-python-tools/pull/424) ([ml-evs](https://github.com/ml-evs))
- Minor CI updates [\#422](https://github.com/Materials-Consortia/optimade-python-tools/pull/422) ([CasperWA](https://github.com/CasperWA))
- Add `api_hint` query parameter [\#421](https://github.com/Materials-Consortia/optimade-python-tools/pull/421) ([CasperWA](https://github.com/CasperWA))
- Implement 553 Version Not Supported [\#420](https://github.com/Materials-Consortia/optimade-python-tools/pull/420) ([CasperWA](https://github.com/CasperWA))
- Fix incorrect placement of header=present in versions endpoint [\#419](https://github.com/Materials-Consortia/optimade-python-tools/pull/419) ([ml-evs](https://github.com/ml-evs))
- Bump optimade-version.json to 1.0.0 [\#416](https://github.com/Materials-Consortia/optimade-python-tools/pull/416) ([ml-evs](https://github.com/ml-evs))
- Use optimade-validator-action v2 [\#413](https://github.com/Materials-Consortia/optimade-python-tools/pull/413) ([CasperWA](https://github.com/CasperWA))
- Bump providers from `a96d424` to `52027b1` [\#389](https://github.com/Materials-Consortia/optimade-python-tools/pull/389) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.10.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.10.0) (2020-07-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.8...v0.10.0)

**Implemented enhancements:**

- Move tests to pytest system from unittest [\#270](https://github.com/Materials-Consortia/optimade-python-tools/issues/270)

**Fixed bugs:**

- Fix /vMAJOR/info in index server [\#414](https://github.com/Materials-Consortia/optimade-python-tools/pull/414) ([CasperWA](https://github.com/CasperWA))

**Closed issues:**

- Validation of 'structures' type crashes [\#397](https://github.com/Materials-Consortia/optimade-python-tools/issues/397)
- Validator verbosity levels need more detailed description [\#396](https://github.com/Materials-Consortia/optimade-python-tools/issues/396)
- Validator treats top-level 'included' array as mandatory [\#393](https://github.com/Materials-Consortia/optimade-python-tools/issues/393)
- \(Un\)versioned URLs [\#379](https://github.com/Materials-Consortia/optimade-python-tools/issues/379)

**Merged pull requests:**

- Temporarily run AiiDA tests on Python 3.8 only [\#400](https://github.com/Materials-Consortia/optimade-python-tools/pull/400) ([ml-evs](https://github.com/ml-evs))
- Make the example for --as\_type more similar to a real use case [\#398](https://github.com/Materials-Consortia/optimade-python-tools/pull/398) ([merkys](https://github.com/merkys))
- Fix some validator-specific crashes [\#395](https://github.com/Materials-Consortia/optimade-python-tools/pull/395) ([ml-evs](https://github.com/ml-evs))
- Use pytest instead of unittest [\#390](https://github.com/Materials-Consortia/optimade-python-tools/pull/390) ([CasperWA](https://github.com/CasperWA))

## [v0.9.8](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.8) (2020-07-03)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.7...v0.9.8)

**Implemented enhancements:**

- Set implementation version in config by default [\#385](https://github.com/Materials-Consortia/optimade-python-tools/pull/385) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- Update models, endpoints and responses to 1.0.0 [\#380](https://github.com/Materials-Consortia/optimade-python-tools/pull/380) ([ml-evs](https://github.com/ml-evs))

## [v0.9.7](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.7) (2020-06-28)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.6...v0.9.7)

## [v0.9.6](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.6) (2020-06-28)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.5...v0.9.6)

**Fixed bugs:**

- Fix publish workflow - final\(TM\) fix [\#378](https://github.com/Materials-Consortia/optimade-python-tools/pull/378) ([CasperWA](https://github.com/CasperWA))

## [v0.9.5](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.5) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.4...v0.9.5)

## [v0.9.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.4) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.3...v0.9.4)

## [v0.9.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.3) (2020-06-26)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.2...v0.9.3)

**Merged pull requests:**

- Fix version issues in the publish workflow [\#376](https://github.com/Materials-Consortia/optimade-python-tools/pull/376) ([shyamd](https://github.com/shyamd))
- Bump providers from `732593a` to `a96d424` [\#368](https://github.com/Materials-Consortia/optimade-python-tools/pull/368) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.9.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.2) (2020-06-25)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.1...v0.9.2)

**Fixed bugs:**

- Heroku cannot handle submodules when deploying via GitHub [\#373](https://github.com/Materials-Consortia/optimade-python-tools/issues/373)

**Closed issues:**

- Updates to models \(new OPTIONAL `type` field under `properties`\) [\#345](https://github.com/Materials-Consortia/optimade-python-tools/issues/345)
- Add aggregatation fields to links model [\#344](https://github.com/Materials-Consortia/optimade-python-tools/issues/344)
- Updates to models \(nperiodic\_dimensions\) [\#343](https://github.com/Materials-Consortia/optimade-python-tools/issues/343)
- Updates to models \(changing unknown atoms\) [\#342](https://github.com/Materials-Consortia/optimade-python-tools/issues/342)
- Improvements/fixes for openapi.json [\#332](https://github.com/Materials-Consortia/optimade-python-tools/issues/332)
- Update to v1.0.0-rc.1 [\#329](https://github.com/Materials-Consortia/optimade-python-tools/issues/329)
- RST not rendering with mkdocs [\#307](https://github.com/Materials-Consortia/optimade-python-tools/issues/307)

**Merged pull requests:**

- Retrieve providers list if no submodule is found [\#374](https://github.com/Materials-Consortia/optimade-python-tools/pull/374) ([CasperWA](https://github.com/CasperWA))
- Update default implementation information [\#372](https://github.com/Materials-Consortia/optimade-python-tools/pull/372) ([shyamd](https://github.com/shyamd))
- Bump spec version to 1.0.0-rc.2 [\#367](https://github.com/Materials-Consortia/optimade-python-tools/pull/367) ([ml-evs](https://github.com/ml-evs))
- Merge all Dependabot updates [\#353](https://github.com/Materials-Consortia/optimade-python-tools/pull/353) ([shyamd](https://github.com/shyamd))
- Update model descriptions and openapi.json for 1.0.0-rc2 [\#351](https://github.com/Materials-Consortia/optimade-python-tools/pull/351) ([ml-evs](https://github.com/ml-evs))
- Update models according to changes during CECAM 2020 meeting [\#350](https://github.com/Materials-Consortia/optimade-python-tools/pull/350) ([ml-evs](https://github.com/ml-evs))
- Decouple changes in providers repo [\#312](https://github.com/Materials-Consortia/optimade-python-tools/pull/312) ([shyamd](https://github.com/shyamd))

## [v0.9.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.1) (2020-06-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.9.0...v0.9.1)

## [v0.9.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.9.0) (2020-06-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.8.1...v0.9.0)

**Implemented enhancements:**

- Breaking up the python tools into seperable packages [\#255](https://github.com/Materials-Consortia/optimade-python-tools/issues/255)
- Run both servers as standard [\#238](https://github.com/Materials-Consortia/optimade-python-tools/issues/238)

**Fixed bugs:**

- Non-running CI job [\#331](https://github.com/Materials-Consortia/optimade-python-tools/issues/331)
- Special species "X" not tested for non-disordered structures [\#304](https://github.com/Materials-Consortia/optimade-python-tools/issues/304)
- Standardize timezone of datetime responses [\#288](https://github.com/Materials-Consortia/optimade-python-tools/issues/288)
- Queries on aliased/provider fields are broken for nested properties [\#282](https://github.com/Materials-Consortia/optimade-python-tools/issues/282)
- General exceptions not being put into response [\#281](https://github.com/Materials-Consortia/optimade-python-tools/issues/281)
- Issue with CIF export [\#271](https://github.com/Materials-Consortia/optimade-python-tools/issues/271)
- Type-cast inputs for general Error [\#280](https://github.com/Materials-Consortia/optimade-python-tools/pull/280) ([CasperWA](https://github.com/CasperWA))

**Closed issues:**

- Update links resources [\#299](https://github.com/Materials-Consortia/optimade-python-tools/issues/299)
- Need to set up mkdocs [\#289](https://github.com/Materials-Consortia/optimade-python-tools/issues/289)
- Need to add custom schema entries for unit/sortable \(and eventually type\) [\#278](https://github.com/Materials-Consortia/optimade-python-tools/issues/278)
- /info/\<entry-endpoint\> missing `sortable` key under each property [\#273](https://github.com/Materials-Consortia/optimade-python-tools/issues/273)
- Make CI linting more useful [\#269](https://github.com/Materials-Consortia/optimade-python-tools/issues/269)
- \[PR SPECIFIC\] Reminder: Validator test pinned to specific commit [\#268](https://github.com/Materials-Consortia/optimade-python-tools/issues/268)
- Validator does not check that pagination links work [\#265](https://github.com/Materials-Consortia/optimade-python-tools/issues/265)
- available\_api\_versions is not correctly validated [\#261](https://github.com/Materials-Consortia/optimade-python-tools/issues/261)
- Implementation model should allow for any URL type in `source_url` [\#260](https://github.com/Materials-Consortia/optimade-python-tools/issues/260)
- Extra structure endpoints in the api specification @ odbx [\#259](https://github.com/Materials-Consortia/optimade-python-tools/issues/259)
- Wrong response structure at info endpoint @ cod [\#258](https://github.com/Materials-Consortia/optimade-python-tools/issues/258)
- Missing base url for api's docs @ materialscloud [\#257](https://github.com/Materials-Consortia/optimade-python-tools/issues/257)
- Handling of KNOWN in mongo backend [\#254](https://github.com/Materials-Consortia/optimade-python-tools/issues/254)
- `None` values in `lattice_vectors` [\#170](https://github.com/Materials-Consortia/optimade-python-tools/issues/170)
- Make sure that the PyPI distribution works [\#143](https://github.com/Materials-Consortia/optimade-python-tools/issues/143)
- Move run.sh to a python file to be environment-agnostic [\#81](https://github.com/Materials-Consortia/optimade-python-tools/issues/81)

**Merged pull requests:**

- Another fix for release pipeline [\#355](https://github.com/Materials-Consortia/optimade-python-tools/pull/355) ([shyamd](https://github.com/shyamd))
- Fix publish workflow [\#354](https://github.com/Materials-Consortia/optimade-python-tools/pull/354) ([CasperWA](https://github.com/CasperWA))
- Fix publish workflow [\#352](https://github.com/Materials-Consortia/optimade-python-tools/pull/352) ([CasperWA](https://github.com/CasperWA))
- Update publish workflow [\#340](https://github.com/Materials-Consortia/optimade-python-tools/pull/340) ([shyamd](https://github.com/shyamd))
- Remove test publish action [\#338](https://github.com/Materials-Consortia/optimade-python-tools/pull/338) ([shyamd](https://github.com/shyamd))
- Fix 'publish\_TestPyPI' CI job [\#337](https://github.com/Materials-Consortia/optimade-python-tools/pull/337) ([CasperWA](https://github.com/CasperWA))
- Represent the datetime objects as UTC in RFC3339 format [\#333](https://github.com/Materials-Consortia/optimade-python-tools/pull/333) ([fekad](https://github.com/fekad))
- dependamat: Bump \<package\_name\> v x.y.z to vx.y.\(z+1\) [\#330](https://github.com/Materials-Consortia/optimade-python-tools/pull/330) ([ml-evs](https://github.com/ml-evs))
- Update links resources [\#306](https://github.com/Materials-Consortia/optimade-python-tools/pull/306) ([CasperWA](https://github.com/CasperWA))
- Add special species for adapters testing [\#305](https://github.com/Materials-Consortia/optimade-python-tools/pull/305) ([CasperWA](https://github.com/CasperWA))
- Clean Up Build Environment [\#301](https://github.com/Materials-Consortia/optimade-python-tools/pull/301) ([shyamd](https://github.com/shyamd))
- Enable CI failures for linting [\#300](https://github.com/Materials-Consortia/optimade-python-tools/pull/300) ([ml-evs](https://github.com/ml-evs))
- Adding jarvis-tools structures [\#297](https://github.com/Materials-Consortia/optimade-python-tools/pull/297) ([knc6](https://github.com/knc6))
- Update Docs [\#295](https://github.com/Materials-Consortia/optimade-python-tools/pull/295) ([shyamd](https://github.com/shyamd))
- Setup MKDocs for Documentation [\#294](https://github.com/Materials-Consortia/optimade-python-tools/pull/294) ([shyamd](https://github.com/shyamd))
- Fix filters on nested provider/aliased fields [\#285](https://github.com/Materials-Consortia/optimade-python-tools/pull/285) ([ml-evs](https://github.com/ml-evs))
- Use heroku-shields instead of heroku-badge [\#284](https://github.com/Materials-Consortia/optimade-python-tools/pull/284) ([CasperWA](https://github.com/CasperWA))
- Add OPTIMADE logo to badge by extending JSON [\#283](https://github.com/Materials-Consortia/optimade-python-tools/pull/283) ([CasperWA](https://github.com/CasperWA))
- Add null check to mongo filtertransformer for KNOWN/UNKNOWN filters [\#279](https://github.com/Materials-Consortia/optimade-python-tools/pull/279) ([ml-evs](https://github.com/ml-evs))
- Add `sortable=True` to all properties [\#274](https://github.com/Materials-Consortia/optimade-python-tools/pull/274) ([CasperWA](https://github.com/CasperWA))
- Make \_atom\_site\_label unique in CIF generation [\#272](https://github.com/Materials-Consortia/optimade-python-tools/pull/272) ([CasperWA](https://github.com/CasperWA))
- Not so quick fix to allow "/" at end of validator URL, plus fixes and tests for --as\_type [\#267](https://github.com/Materials-Consortia/optimade-python-tools/pull/267) ([ml-evs](https://github.com/ml-evs))
- Check pagination links-\>next with validator [\#266](https://github.com/Materials-Consortia/optimade-python-tools/pull/266) ([ml-evs](https://github.com/ml-evs))
- Relax HTTP URL constraints on meta-\>implementation-\>source\_url field. [\#262](https://github.com/Materials-Consortia/optimade-python-tools/pull/262) ([ml-evs](https://github.com/ml-evs))
- Validate lattice\_vectors for all null or all float [\#171](https://github.com/Materials-Consortia/optimade-python-tools/pull/171) ([CasperWA](https://github.com/CasperWA))

## [v0.8.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.8.1) (2020-04-25)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.8.0...v0.8.1)

**Fixed bugs:**

- Pip install missing some files [\#252](https://github.com/Materials-Consortia/optimade-python-tools/issues/252)

**Merged pull requests:**

- v0.8.1 hotfix [\#256](https://github.com/Materials-Consortia/optimade-python-tools/pull/256) ([ml-evs](https://github.com/ml-evs))
- Fix 252 missing landing page [\#253](https://github.com/Materials-Consortia/optimade-python-tools/pull/253) ([shyamd](https://github.com/shyamd))

## [v0.8.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.8.0) (2020-04-22)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.7.1...v0.8.0)

**Implemented enhancements:**

- Switch to pydantic's BaseSettings for the config file? [\#152](https://github.com/Materials-Consortia/optimade-python-tools/issues/152)
- Remove query constraints for /links-endpoint [\#244](https://github.com/Materials-Consortia/optimade-python-tools/pull/244) ([CasperWA](https://github.com/CasperWA))
- Add adapters - Base design + 'structures' \(+ 'references'... sort of\) [\#241](https://github.com/Materials-Consortia/optimade-python-tools/pull/241) ([CasperWA](https://github.com/CasperWA))
- Add dependabot and last commit date badges [\#237](https://github.com/Materials-Consortia/optimade-python-tools/pull/237) ([CasperWA](https://github.com/CasperWA))
- Add mongo length operator functionality with length aliases [\#222](https://github.com/Materials-Consortia/optimade-python-tools/pull/222) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Use Path.home\(\) instead of ~ in default config path values [\#245](https://github.com/Materials-Consortia/optimade-python-tools/issues/245)

**Closed issues:**

- Have Dependabot take care of various requirements.txt files as well [\#249](https://github.com/Materials-Consortia/optimade-python-tools/issues/249)
- Remove commented out GH Action job `deps_clean-install` [\#247](https://github.com/Materials-Consortia/optimade-python-tools/issues/247)
- Local testing fails without default config [\#239](https://github.com/Materials-Consortia/optimade-python-tools/issues/239)
- Release only when pushing to master [\#229](https://github.com/Materials-Consortia/optimade-python-tools/issues/229)
- Do we need `server.cfg`? [\#134](https://github.com/Materials-Consortia/optimade-python-tools/issues/134)
- Implement LENGTH in query [\#86](https://github.com/Materials-Consortia/optimade-python-tools/issues/86)

**Merged pull requests:**

- Up to v0.8.0 [\#251](https://github.com/Materials-Consortia/optimade-python-tools/pull/251) ([CasperWA](https://github.com/CasperWA))
- Remove old commented GH Action job [\#250](https://github.com/Materials-Consortia/optimade-python-tools/pull/250) ([CasperWA](https://github.com/CasperWA))
- Use Path.home\(\) instead of `~` [\#246](https://github.com/Materials-Consortia/optimade-python-tools/pull/246) ([CasperWA](https://github.com/CasperWA))
- Fix path in default config [\#243](https://github.com/Materials-Consortia/optimade-python-tools/pull/243) ([ml-evs](https://github.com/ml-evs))
- Fixes Local Tests [\#240](https://github.com/Materials-Consortia/optimade-python-tools/pull/240) ([shyamd](https://github.com/shyamd))
- Revert "Fix github actions for non-release tags" [\#236](https://github.com/Materials-Consortia/optimade-python-tools/pull/236) ([shyamd](https://github.com/shyamd))
- Enable filtering on relationships with mongo  [\#234](https://github.com/Materials-Consortia/optimade-python-tools/pull/234) ([ml-evs](https://github.com/ml-evs))
- Update filter examples and validate optional cases [\#227](https://github.com/Materials-Consortia/optimade-python-tools/pull/227) ([ml-evs](https://github.com/ml-evs))
- Switch from config init to BaseSettings [\#226](https://github.com/Materials-Consortia/optimade-python-tools/pull/226) ([shyamd](https://github.com/shyamd))

## [v0.7.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.7.1) (2020-03-16)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.7.0...v0.7.1)

**Closed issues:**

- Fix all capitalisation of OPTIMADE [\#232](https://github.com/Materials-Consortia/optimade-python-tools/issues/232)
- Remove validator action from README [\#230](https://github.com/Materials-Consortia/optimade-python-tools/issues/230)

**Merged pull requests:**

- Fix github actions for non-release tags [\#235](https://github.com/Materials-Consortia/optimade-python-tools/pull/235) ([shyamd](https://github.com/shyamd))
- Update OPTIMADE capitalisation [\#233](https://github.com/Materials-Consortia/optimade-python-tools/pull/233) ([ml-evs](https://github.com/ml-evs))
- Update mentions of action in readme [\#231](https://github.com/Materials-Consortia/optimade-python-tools/pull/231) ([ml-evs](https://github.com/ml-evs))

## [v0.7.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.7.0) (2020-03-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.6.0...v0.7.0)

**Implemented enhancements:**

- Validate all non-optional :filter: examples from the spec [\#213](https://github.com/Materials-Consortia/optimade-python-tools/pull/213) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Some mandatory filter examples from spec do not work [\#217](https://github.com/Materials-Consortia/optimade-python-tools/issues/217)
- Add txt-files in optimade.validator.data to MANIFEST [\#225](https://github.com/Materials-Consortia/optimade-python-tools/pull/225) ([CasperWA](https://github.com/CasperWA))
- Handle arbitrary nested NOT/AND/OR in queries [\#221](https://github.com/Materials-Consortia/optimade-python-tools/pull/221) ([ml-evs](https://github.com/ml-evs))

**Closed issues:**

- Validator only validates what we have working, not what is required by the spec [\#182](https://github.com/Materials-Consortia/optimade-python-tools/issues/182)

**Merged pull requests:**

- v0.7.0 release [\#228](https://github.com/Materials-Consortia/optimade-python-tools/pull/228) ([ml-evs](https://github.com/ml-evs))
- Remove GH Action to validate OPTiMaDe instances [\#224](https://github.com/Materials-Consortia/optimade-python-tools/pull/224) ([CasperWA](https://github.com/CasperWA))

## [v0.6.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.6.0) (2020-03-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.5.0...v0.6.0)

**Implemented enhancements:**

- Possibly add CORS middleware [\#159](https://github.com/Materials-Consortia/optimade-python-tools/issues/159)
- Add debug flag to server [\#130](https://github.com/Materials-Consortia/optimade-python-tools/issues/130)
- Make validator GitHub Action [\#191](https://github.com/Materials-Consortia/optimade-python-tools/pull/191) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- meta/query/representation value not cutting off version properly [\#199](https://github.com/Materials-Consortia/optimade-python-tools/issues/199)
- URL for providers.json from Materials-Consortia has changed [\#186](https://github.com/Materials-Consortia/optimade-python-tools/issues/186)
- Relationships don't work when "/" present in id [\#181](https://github.com/Materials-Consortia/optimade-python-tools/issues/181)
- Redirect middleware not hitting single-entry endpoints [\#174](https://github.com/Materials-Consortia/optimade-python-tools/issues/174)

**Closed issues:**

- /info/ reports wrong url under available\_api\_versions [\#215](https://github.com/Materials-Consortia/optimade-python-tools/issues/215)
- Query parameters not handled correctly [\#208](https://github.com/Materials-Consortia/optimade-python-tools/issues/208)
- Test for AvailableApiVersion is correct for the wrong reasons [\#204](https://github.com/Materials-Consortia/optimade-python-tools/issues/204)
- Drop '/optimade' from paths in openapi.json [\#197](https://github.com/Materials-Consortia/optimade-python-tools/issues/197)
- heroku is failing [\#185](https://github.com/Materials-Consortia/optimade-python-tools/issues/185)
- List properties and HAS \_ operators missing [\#98](https://github.com/Materials-Consortia/optimade-python-tools/issues/98)
- Checklist for OPTiMaDe v0.10.1 [\#29](https://github.com/Materials-Consortia/optimade-python-tools/issues/29)

**Merged pull requests:**

- Removed /optimade/ prefix in info response [\#216](https://github.com/Materials-Consortia/optimade-python-tools/pull/216) ([ml-evs](https://github.com/ml-evs))
- Self load data [\#212](https://github.com/Materials-Consortia/optimade-python-tools/pull/212) ([shyamd](https://github.com/shyamd))
- Update tests for available\_api\_versions [\#211](https://github.com/Materials-Consortia/optimade-python-tools/pull/211) ([CasperWA](https://github.com/CasperWA))
- Up to v0.6.0 [\#210](https://github.com/Materials-Consortia/optimade-python-tools/pull/210) ([CasperWA](https://github.com/CasperWA))
- Update handling of include parameter \(and other query parameters\) [\#209](https://github.com/Materials-Consortia/optimade-python-tools/pull/209) ([CasperWA](https://github.com/CasperWA))
- Skip HAS ONLY test if mongomock version \<= 3.19.0 [\#206](https://github.com/Materials-Consortia/optimade-python-tools/pull/206) ([ml-evs](https://github.com/ml-evs))
- Test mandatory queries in validator [\#205](https://github.com/Materials-Consortia/optimade-python-tools/pull/205) ([ml-evs](https://github.com/ml-evs))
- Fix include query parameter [\#202](https://github.com/Materials-Consortia/optimade-python-tools/pull/202) ([CasperWA](https://github.com/CasperWA))
- Fix meta.query.representation and remove /optimade in base URLs [\#201](https://github.com/Materials-Consortia/optimade-python-tools/pull/201) ([CasperWA](https://github.com/CasperWA))
- Use mongo for CI [\#196](https://github.com/Materials-Consortia/optimade-python-tools/pull/196) ([ml-evs](https://github.com/ml-evs))
- \(Cosmetic\) updates to models [\#195](https://github.com/Materials-Consortia/optimade-python-tools/pull/195) ([CasperWA](https://github.com/CasperWA))
- Add CORSMiddleware [\#194](https://github.com/Materials-Consortia/optimade-python-tools/pull/194) ([CasperWA](https://github.com/CasperWA))
- Add "debug mode" [\#190](https://github.com/Materials-Consortia/optimade-python-tools/pull/190) ([CasperWA](https://github.com/CasperWA))
- Use https://provider.optimade.org/providers.json [\#187](https://github.com/Materials-Consortia/optimade-python-tools/pull/187) ([CasperWA](https://github.com/CasperWA))
- Fix errors parsing IDs that contain slashes [\#183](https://github.com/Materials-Consortia/optimade-python-tools/pull/183) ([ml-evs](https://github.com/ml-evs))
- Added default mongo implementations for HAS ALL/ANY/ONLY [\#173](https://github.com/Materials-Consortia/optimade-python-tools/pull/173) ([ml-evs](https://github.com/ml-evs))

## [v0.5.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.5.0) (2020-02-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.4.0...v0.5.0)

**Implemented enhancements:**

- Implement a landing page for requests to the base URL [\#169](https://github.com/Materials-Consortia/optimade-python-tools/issues/169)

**Fixed bugs:**

- 'minor' and 'patch' versioned base URL prefixes are wrong [\#177](https://github.com/Materials-Consortia/optimade-python-tools/issues/177)

**Closed issues:**

- Handle `include` standard JSON API query parameter [\#94](https://github.com/Materials-Consortia/optimade-python-tools/issues/94)

**Merged pull requests:**

- Bump to v0.5.0 [\#179](https://github.com/Materials-Consortia/optimade-python-tools/pull/179) ([CasperWA](https://github.com/CasperWA))
- Correctly create optional versioned base URLs [\#178](https://github.com/Materials-Consortia/optimade-python-tools/pull/178) ([CasperWA](https://github.com/CasperWA))
- Make mapper aliases configurable [\#175](https://github.com/Materials-Consortia/optimade-python-tools/pull/175) ([ml-evs](https://github.com/ml-evs))
- Add landing page at base URL [\#172](https://github.com/Materials-Consortia/optimade-python-tools/pull/172) ([ml-evs](https://github.com/ml-evs))
- Implement `include` query parameter [\#163](https://github.com/Materials-Consortia/optimade-python-tools/pull/163) ([CasperWA](https://github.com/CasperWA))
- Add docker for index meta-database [\#140](https://github.com/Materials-Consortia/optimade-python-tools/pull/140) ([CasperWA](https://github.com/CasperWA))

## [v0.4.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.4.0) (2020-02-06)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.4...v0.4.0)

**Implemented enhancements:**

- switch to pipenv? [\#37](https://github.com/Materials-Consortia/optimade-python-tools/issues/37)
- Reorder tests [\#162](https://github.com/Materials-Consortia/optimade-python-tools/pull/162) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Server app intermingles [\#161](https://github.com/Materials-Consortia/optimade-python-tools/issues/161)
- `response_fields` not working [\#154](https://github.com/Materials-Consortia/optimade-python-tools/issues/154)

**Closed issues:**

- Change `page_page` to `page_number` [\#165](https://github.com/Materials-Consortia/optimade-python-tools/issues/165)
- Add schema-relevant parameters to query parameters [\#164](https://github.com/Materials-Consortia/optimade-python-tools/issues/164)
- Alias optimade/structures/ to optimade/structure [\#128](https://github.com/Materials-Consortia/optimade-python-tools/issues/128)
- Minor changes to specification v0.10.1-develop [\#115](https://github.com/Materials-Consortia/optimade-python-tools/issues/115)
- Update models with new levels of REQUIRED response properties [\#114](https://github.com/Materials-Consortia/optimade-python-tools/issues/114)
- Constraining list/array types in the schema [\#55](https://github.com/Materials-Consortia/optimade-python-tools/issues/55)

**Merged pull requests:**

- Bump to v0.4.0 [\#168](https://github.com/Materials-Consortia/optimade-python-tools/pull/168) ([CasperWA](https://github.com/CasperWA))
- Describe query parameters in OpenAPI schema [\#166](https://github.com/Materials-Consortia/optimade-python-tools/pull/166) ([CasperWA](https://github.com/CasperWA))
- Redirect slashed URLs [\#160](https://github.com/Materials-Consortia/optimade-python-tools/pull/160) ([CasperWA](https://github.com/CasperWA))
- New REQUIRED level properties [\#153](https://github.com/Materials-Consortia/optimade-python-tools/pull/153) ([CasperWA](https://github.com/CasperWA))

## [v0.3.4](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.4) (2020-02-04)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.3...v0.3.4)

**Implemented enhancements:**

- Include `develop` or not? Default branch? - Create INSTALL.md [\#136](https://github.com/Materials-Consortia/optimade-python-tools/issues/136)

**Fixed bugs:**

- Excepting non-existent exception [\#129](https://github.com/Materials-Consortia/optimade-python-tools/issues/129)

**Closed issues:**

- disable serving API under /v0.10 and /v0.10.0 by default? [\#122](https://github.com/Materials-Consortia/optimade-python-tools/issues/122)
- PyPI release checklist [\#67](https://github.com/Materials-Consortia/optimade-python-tools/issues/67)

**Merged pull requests:**

- Bump to v0.3.4 [\#158](https://github.com/Materials-Consortia/optimade-python-tools/pull/158) ([CasperWA](https://github.com/CasperWA))
- Fix heroku badge [\#157](https://github.com/Materials-Consortia/optimade-python-tools/pull/157) ([ml-evs](https://github.com/ml-evs))
- Move installation instructions [\#156](https://github.com/Materials-Consortia/optimade-python-tools/pull/156) ([ml-evs](https://github.com/ml-evs))
- Update base URLs [\#155](https://github.com/Materials-Consortia/optimade-python-tools/pull/155) ([CasperWA](https://github.com/CasperWA))
- Extend OpenAPI/spec description [\#151](https://github.com/Materials-Consortia/optimade-python-tools/pull/151) ([CasperWA](https://github.com/CasperWA))
- Non Local Mongo [\#150](https://github.com/Materials-Consortia/optimade-python-tools/pull/150) ([shyamd](https://github.com/shyamd))

## [v0.3.3](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.3) (2020-01-24)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.2...v0.3.3)

**Fixed bugs:**

- Lark files not being distributed [\#141](https://github.com/Materials-Consortia/optimade-python-tools/issues/141)

**Merged pull requests:**

- Updated lark-parser to 0.8.1 [\#149](https://github.com/Materials-Consortia/optimade-python-tools/pull/149) ([ml-evs](https://github.com/ml-evs))
- Split eager and standard tests to avoid unnecessary badge of shame [\#148](https://github.com/Materials-Consortia/optimade-python-tools/pull/148) ([ml-evs](https://github.com/ml-evs))
- Bump to v0.3.3 [\#147](https://github.com/Materials-Consortia/optimade-python-tools/pull/147) ([CasperWA](https://github.com/CasperWA))
- Fix root\_validator issues with optional fields and made meta optional [\#145](https://github.com/Materials-Consortia/optimade-python-tools/pull/145) ([ml-evs](https://github.com/ml-evs))
- Handle `JSONDecodeError`s in validator [\#144](https://github.com/Materials-Consortia/optimade-python-tools/pull/144) ([ml-evs](https://github.com/ml-evs))

## [v0.3.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.2) (2020-01-20)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.1...v0.3.2)

**Implemented enhancements:**

- Add base URL to configuration file [\#135](https://github.com/Materials-Consortia/optimade-python-tools/pull/135) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Fix `load_from_json` [\#137](https://github.com/Materials-Consortia/optimade-python-tools/pull/137) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- Make sure relevant package data is included in distributions [\#142](https://github.com/Materials-Consortia/optimade-python-tools/pull/142) ([CasperWA](https://github.com/CasperWA))
- Add database page limit [\#139](https://github.com/Materials-Consortia/optimade-python-tools/pull/139) ([CasperWA](https://github.com/CasperWA))

## [v0.3.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.1) (2020-01-17)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.3.0...v0.3.1)

**Merged pull requests:**

- Update requirements [\#138](https://github.com/Materials-Consortia/optimade-python-tools/pull/138) ([CasperWA](https://github.com/CasperWA))

## [v0.3.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.3.0) (2020-01-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.2...v0.3.0)

**Implemented enhancements:**

- Implement optional `implementation` in top-level meta response [\#117](https://github.com/Materials-Consortia/optimade-python-tools/issues/117)
- Create "special" index meta-database server [\#100](https://github.com/Materials-Consortia/optimade-python-tools/issues/100)
- Implement relationships in server [\#71](https://github.com/Materials-Consortia/optimade-python-tools/issues/71)
- Add missing /references endpoint to server [\#69](https://github.com/Materials-Consortia/optimade-python-tools/issues/69)
- Automatically publish version tags to PyPI via GH Actions [\#107](https://github.com/Materials-Consortia/optimade-python-tools/pull/107) ([CasperWA](https://github.com/CasperWA))
- Using routers [\#99](https://github.com/Materials-Consortia/optimade-python-tools/pull/99) ([CasperWA](https://github.com/CasperWA))
- Add relationships functionality [\#91](https://github.com/Materials-Consortia/optimade-python-tools/pull/91) ([ml-evs](https://github.com/ml-evs))
- Added external API validator based on our pydantic models [\#74](https://github.com/Materials-Consortia/optimade-python-tools/pull/74) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- The invoke task `update-openapijson` is incomplete [\#123](https://github.com/Materials-Consortia/optimade-python-tools/issues/123)
- Django vulnerability [\#108](https://github.com/Materials-Consortia/optimade-python-tools/issues/108)

**Closed issues:**

- info endpoint duplicated? [\#120](https://github.com/Materials-Consortia/optimade-python-tools/issues/120)
- Commented-out validator [\#111](https://github.com/Materials-Consortia/optimade-python-tools/issues/111)
- FastAPI v0.44.0 supports pydantic \> 1.0.0 [\#101](https://github.com/Materials-Consortia/optimade-python-tools/issues/101)
- Server is missing /links endpoint [\#89](https://github.com/Materials-Consortia/optimade-python-tools/issues/89)
- Make sure all validators are tested [\#87](https://github.com/Materials-Consortia/optimade-python-tools/issues/87)
- The `sortable` field must be added to models [\#84](https://github.com/Materials-Consortia/optimade-python-tools/issues/84)
- Package structure [\#72](https://github.com/Materials-Consortia/optimade-python-tools/issues/72)
- Possibly make /info/{endpoint} dynamic [\#70](https://github.com/Materials-Consortia/optimade-python-tools/issues/70)
- setuptools package with server as "extra" [\#62](https://github.com/Materials-Consortia/optimade-python-tools/issues/62)
- use examples from specs as resources [\#57](https://github.com/Materials-Consortia/optimade-python-tools/issues/57)
- httptools dependency has build issues on GCC/Linux [\#54](https://github.com/Materials-Consortia/optimade-python-tools/issues/54)
- Lark grammar file for v0.9.8 [\#50](https://github.com/Materials-Consortia/optimade-python-tools/issues/50)
- type is missing in response [\#43](https://github.com/Materials-Consortia/optimade-python-tools/issues/43)
- Enforce use of autoformatter  [\#33](https://github.com/Materials-Consortia/optimade-python-tools/issues/33)
- switch license to MIT [\#28](https://github.com/Materials-Consortia/optimade-python-tools/issues/28)
- write a lark JSONTransformer / JSONdecoder [\#26](https://github.com/Materials-Consortia/optimade-python-tools/issues/26)
- server.jsonapi has no additionalProperties=false  [\#23](https://github.com/Materials-Consortia/optimade-python-tools/issues/23)
- server.jsonapi has no patternProperties  [\#22](https://github.com/Materials-Consortia/optimade-python-tools/issues/22)
- Developer-friendly pre-commit openapi.json visual diff [\#21](https://github.com/Materials-Consortia/optimade-python-tools/issues/21)
- add JSON schema API [\#12](https://github.com/Materials-Consortia/optimade-python-tools/issues/12)
- generate static documentation on github from openapi.json [\#9](https://github.com/Materials-Consortia/optimade-python-tools/issues/9)
- test how to generate a client from the openapi.json [\#8](https://github.com/Materials-Consortia/optimade-python-tools/issues/8)
- come up with suggested toolchain for validating existing optimade API against openapi.json [\#7](https://github.com/Materials-Consortia/optimade-python-tools/issues/7)
- add travis test that checks openapi.json is valid OpenAPI spec [\#6](https://github.com/Materials-Consortia/optimade-python-tools/issues/6)
- add 2 examples of how to include documentation in python classes [\#5](https://github.com/Materials-Consortia/optimade-python-tools/issues/5)
- add one-line command to update openapi.json [\#4](https://github.com/Materials-Consortia/optimade-python-tools/issues/4)

**Merged pull requests:**

- Fixed CI readme badge [\#133](https://github.com/Materials-Consortia/optimade-python-tools/pull/133) ([ml-evs](https://github.com/ml-evs))
- Add meta.description to BaseRelationshipResource [\#131](https://github.com/Materials-Consortia/optimade-python-tools/pull/131) ([CasperWA](https://github.com/CasperWA))
- Added homepage attribute to LinksResource [\#127](https://github.com/Materials-Consortia/optimade-python-tools/pull/127) ([ml-evs](https://github.com/ml-evs))
- Updated structure models and validators [\#126](https://github.com/Materials-Consortia/optimade-python-tools/pull/126) ([ml-evs](https://github.com/ml-evs))
- Minor change to fallback server.cfg [\#125](https://github.com/Materials-Consortia/optimade-python-tools/pull/125) ([ml-evs](https://github.com/ml-evs))
- Update local OpenAPI schemes prior to copying [\#124](https://github.com/Materials-Consortia/optimade-python-tools/pull/124) ([CasperWA](https://github.com/CasperWA))
- Update OpenAPI tags [\#121](https://github.com/Materials-Consortia/optimade-python-tools/pull/121) ([CasperWA](https://github.com/CasperWA))
- A few fixes related to usage as a library [\#119](https://github.com/Materials-Consortia/optimade-python-tools/pull/119) ([ml-evs](https://github.com/ml-evs))
- Add implementation to top-level meta response [\#118](https://github.com/Materials-Consortia/optimade-python-tools/pull/118) ([CasperWA](https://github.com/CasperWA))
- Add heroku deployment scripts [\#116](https://github.com/Materials-Consortia/optimade-python-tools/pull/116) ([ltalirz](https://github.com/ltalirz))
- Reorganize package [\#113](https://github.com/Materials-Consortia/optimade-python-tools/pull/113) ([CasperWA](https://github.com/CasperWA))
- Introduce grammar v0.10.1 [\#112](https://github.com/Materials-Consortia/optimade-python-tools/pull/112) ([CasperWA](https://github.com/CasperWA))
- Update to pydantic v1 [\#110](https://github.com/Materials-Consortia/optimade-python-tools/pull/110) ([CasperWA](https://github.com/CasperWA))
- Minimum requirement of django v2.2.8 [\#109](https://github.com/Materials-Consortia/optimade-python-tools/pull/109) ([CasperWA](https://github.com/CasperWA))
- Index meta-database [\#103](https://github.com/Materials-Consortia/optimade-python-tools/pull/103) ([CasperWA](https://github.com/CasperWA))
- restrict pydantic version [\#97](https://github.com/Materials-Consortia/optimade-python-tools/pull/97) ([ltalirz](https://github.com/ltalirz))
- Add /links [\#95](https://github.com/Materials-Consortia/optimade-python-tools/pull/95) ([CasperWA](https://github.com/CasperWA))
- Fix data\_returned and data\_available [\#93](https://github.com/Materials-Consortia/optimade-python-tools/pull/93) ([CasperWA](https://github.com/CasperWA))
- Use GitHub Actions for CI [\#92](https://github.com/Materials-Consortia/optimade-python-tools/pull/92) ([ml-evs](https://github.com/ml-evs))
- Remove inappropriate lint messages [\#90](https://github.com/Materials-Consortia/optimade-python-tools/pull/90) ([CasperWA](https://github.com/CasperWA))
- Fix dependencies [\#88](https://github.com/Materials-Consortia/optimade-python-tools/pull/88) ([CasperWA](https://github.com/CasperWA))
- Add sortable field to EntryInfoProperty model [\#85](https://github.com/Materials-Consortia/optimade-python-tools/pull/85) ([CasperWA](https://github.com/CasperWA))
- Validate illegal fields are not present under attributes and relationships [\#83](https://github.com/Materials-Consortia/optimade-python-tools/pull/83) ([CasperWA](https://github.com/CasperWA))
- Add references endpoint [\#78](https://github.com/Materials-Consortia/optimade-python-tools/pull/78) ([CasperWA](https://github.com/CasperWA))
- fix travis build [\#77](https://github.com/Materials-Consortia/optimade-python-tools/pull/77) ([ltalirz](https://github.com/ltalirz))
- Fix manual verification of elements\_ratios [\#76](https://github.com/Materials-Consortia/optimade-python-tools/pull/76) ([CasperWA](https://github.com/CasperWA))
- add automatic PyPI deployment [\#75](https://github.com/Materials-Consortia/optimade-python-tools/pull/75) ([ltalirz](https://github.com/ltalirz))
- Remove reference to `"all"` endpoint and rename collections submodule [\#73](https://github.com/Materials-Consortia/optimade-python-tools/pull/73) ([ml-evs](https://github.com/ml-evs))
- Updates to README and docs for v0.10.0 [\#68](https://github.com/Materials-Consortia/optimade-python-tools/pull/68) ([ml-evs](https://github.com/ml-evs))
- Adding grammar for v0.10.0 [\#66](https://github.com/Materials-Consortia/optimade-python-tools/pull/66) ([fekad](https://github.com/fekad))
- Schema updates and fixes relative to the v0.10.0 spec [\#65](https://github.com/Materials-Consortia/optimade-python-tools/pull/65) ([ml-evs](https://github.com/ml-evs))
- Break requirements down on per backend basis [\#64](https://github.com/Materials-Consortia/optimade-python-tools/pull/64) ([ml-evs](https://github.com/ml-evs))
- 0.10.0 grammer, elasticsearch transformer, setuptools extra [\#63](https://github.com/Materials-Consortia/optimade-python-tools/pull/63) ([markus1978](https://github.com/markus1978))
- Added a Lark to Django Query converter [\#61](https://github.com/Materials-Consortia/optimade-python-tools/pull/61) ([tachyontraveler](https://github.com/tachyontraveler))
- Some minor fixes [\#60](https://github.com/Materials-Consortia/optimade-python-tools/pull/60) ([ml-evs](https://github.com/ml-evs))
- Added codecov to CI [\#59](https://github.com/Materials-Consortia/optimade-python-tools/pull/59) ([ml-evs](https://github.com/ml-evs))
- Enforce black via `pre-commit` tool [\#53](https://github.com/Materials-Consortia/optimade-python-tools/pull/53) ([dwinston](https://github.com/dwinston))
- Update setup.py and version [\#51](https://github.com/Materials-Consortia/optimade-python-tools/pull/51) ([dwinston](https://github.com/dwinston))
- /structure/info endpoint [\#49](https://github.com/Materials-Consortia/optimade-python-tools/pull/49) ([fawzi](https://github.com/fawzi))
- add constrained list type [\#48](https://github.com/Materials-Consortia/optimade-python-tools/pull/48) ([dwinston](https://github.com/dwinston))
- Refactored into submodules and added test data [\#47](https://github.com/Materials-Consortia/optimade-python-tools/pull/47) ([ml-evs](https://github.com/ml-evs))
- Update structure endpoint to pre-alpha 0.10 spec [\#45](https://github.com/Materials-Consortia/optimade-python-tools/pull/45) ([ltalirz](https://github.com/ltalirz))
- Adding Resource Links [\#44](https://github.com/Materials-Consortia/optimade-python-tools/pull/44) ([tpurcell90](https://github.com/tpurcell90))
- Reblacken [\#42](https://github.com/Materials-Consortia/optimade-python-tools/pull/42) ([ml-evs](https://github.com/ml-evs))
- Documented json [\#41](https://github.com/Materials-Consortia/optimade-python-tools/pull/41) ([tpurcell90](https://github.com/tpurcell90))
- fix example output [\#40](https://github.com/Materials-Consortia/optimade-python-tools/pull/40) ([dwinston](https://github.com/dwinston))
- use jsonapi better at top level, add error response [\#36](https://github.com/Materials-Consortia/optimade-python-tools/pull/36) ([fawzi](https://github.com/fawzi))
- add JSONTransformer [\#35](https://github.com/Materials-Consortia/optimade-python-tools/pull/35) ([dwinston](https://github.com/dwinston))
- switch to MIT license [\#34](https://github.com/Materials-Consortia/optimade-python-tools/pull/34) ([ltalirz](https://github.com/ltalirz))
- Updated entry definitions and renamed Response classes [\#32](https://github.com/Materials-Consortia/optimade-python-tools/pull/32) ([ml-evs](https://github.com/ml-evs))
- update readme [\#31](https://github.com/Materials-Consortia/optimade-python-tools/pull/31) ([ltalirz](https://github.com/ltalirz))
- Seperated Links from JSON API into its own file [\#30](https://github.com/Materials-Consortia/optimade-python-tools/pull/30) ([tpurcell90](https://github.com/tpurcell90))
- simplify schema update [\#27](https://github.com/Materials-Consortia/optimade-python-tools/pull/27) ([ltalirz](https://github.com/ltalirz))
- add openapi\_diff to travis [\#25](https://github.com/Materials-Consortia/optimade-python-tools/pull/25) ([ltalirz](https://github.com/ltalirz))
- Json api add [\#24](https://github.com/Materials-Consortia/optimade-python-tools/pull/24) ([tpurcell90](https://github.com/tpurcell90))
- Added JSON diff test [\#20](https://github.com/Materials-Consortia/optimade-python-tools/pull/20) ([ml-evs](https://github.com/ml-evs))
- info endpoint [\#19](https://github.com/Materials-Consortia/optimade-python-tools/pull/19) ([fawzi](https://github.com/fawzi))
- adding run.sh script to start webserver [\#18](https://github.com/Materials-Consortia/optimade-python-tools/pull/18) ([fawzi](https://github.com/fawzi))
- error response [\#17](https://github.com/Materials-Consortia/optimade-python-tools/pull/17) ([fawzi](https://github.com/fawzi))
- Links can be strings [\#16](https://github.com/Materials-Consortia/optimade-python-tools/pull/16) ([fawzi](https://github.com/fawzi))
- response should be either many \(list\) or one \(object\), not an union [\#15](https://github.com/Materials-Consortia/optimade-python-tools/pull/15) ([fawzi](https://github.com/fawzi))
- reorg models [\#14](https://github.com/Materials-Consortia/optimade-python-tools/pull/14) ([dwinston](https://github.com/dwinston))
- Update the OptimadeMetaResponse to development schema [\#13](https://github.com/Materials-Consortia/optimade-python-tools/pull/13) ([ml-evs](https://github.com/ml-evs))
- add openapi spec validator [\#10](https://github.com/Materials-Consortia/optimade-python-tools/pull/10) ([ltalirz](https://github.com/ltalirz))
- fix test data download [\#3](https://github.com/Materials-Consortia/optimade-python-tools/pull/3) ([ltalirz](https://github.com/ltalirz))
- \[WIP\] Mongoconverter [\#1](https://github.com/Materials-Consortia/optimade-python-tools/pull/1) ([wuxiaohua1011](https://github.com/wuxiaohua1011))

## [v0.1.2](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.2) (2018-06-14)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.1...v0.1.2)

## [v0.1.1](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.1) (2018-06-13)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/v0.1.0...v0.1.1)

## [v0.1.0](https://github.com/Materials-Consortia/optimade-python-tools/tree/v0.1.0) (2018-06-05)

[Full Changelog](https://github.com/Materials-Consortia/optimade-python-tools/compare/6680fb28a60ec4ff43a303b7b4dbf41e159a25b6...v0.1.0)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
