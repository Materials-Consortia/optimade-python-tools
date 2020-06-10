# Changelog

## [Unreleased](https://github.com/materials-consortia/optimade-python-tools/tree/HEAD)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.8.1...HEAD)

**Implemented enhancements:**

- Run both servers as standard [\#238](https://github.com/Materials-Consortia/optimade-python-tools/issues/238)

**Fixed bugs:**

- Queries on aliased/provider fields are broken for nested properties [\#282](https://github.com/Materials-Consortia/optimade-python-tools/issues/282)
- General exceptions not being put into response [\#281](https://github.com/Materials-Consortia/optimade-python-tools/issues/281)
- Issue with CIF export [\#271](https://github.com/Materials-Consortia/optimade-python-tools/issues/271)
- Type-cast inputs for general Error [\#280](https://github.com/Materials-Consortia/optimade-python-tools/pull/280) ([CasperWA](https://github.com/CasperWA))

**Security fixes:**

- \[Security\] Bump django from 3.0.4 to 3.0.7 in /.github/workflows [\#291](https://github.com/Materials-Consortia/optimade-python-tools/pull/291) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))

**Closed issues:**

- Need to set up mkdocs [\#289](https://github.com/Materials-Consortia/optimade-python-tools/issues/289)
- Need to add custom schema entries for unit/sortable \(and eventually type\) [\#278](https://github.com/Materials-Consortia/optimade-python-tools/issues/278)
- /info/\<entry-endpoint\> missing `sortable` key under each property [\#273](https://github.com/Materials-Consortia/optimade-python-tools/issues/273)
- Validator does not check that pagination links work [\#265](https://github.com/Materials-Consortia/optimade-python-tools/issues/265)
- available\_api\_versions is not correctly validated [\#261](https://github.com/Materials-Consortia/optimade-python-tools/issues/261)
- Implementation model should allow for any URL type in `source\_url` [\#260](https://github.com/Materials-Consortia/optimade-python-tools/issues/260)
- Extra structure endpoints in the api specification @ odbx [\#259](https://github.com/Materials-Consortia/optimade-python-tools/issues/259)
- Wrong response structure at info endpoint @ cod [\#258](https://github.com/Materials-Consortia/optimade-python-tools/issues/258)
- Missing base url for api's docs @ materialscloud [\#257](https://github.com/Materials-Consortia/optimade-python-tools/issues/257)
- Handling of KNOWN in mongo backend [\#254](https://github.com/Materials-Consortia/optimade-python-tools/issues/254)
- Move run.sh to a python file to be environment-agnostic [\#81](https://github.com/Materials-Consortia/optimade-python-tools/issues/81)

**Merged pull requests:**

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

## [v0.8.1](https://github.com/materials-consortia/optimade-python-tools/tree/v0.8.1) (2020-04-25)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.8.0...v0.8.1)

**Fixed bugs:**

- Pip install missing some files [\#252](https://github.com/Materials-Consortia/optimade-python-tools/issues/252)

**Merged pull requests:**

- v0.8.1 hotfix [\#256](https://github.com/Materials-Consortia/optimade-python-tools/pull/256) ([ml-evs](https://github.com/ml-evs))
- Fix 252 missing landing page [\#253](https://github.com/Materials-Consortia/optimade-python-tools/pull/253) ([shyamd](https://github.com/shyamd))

## [v0.8.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.8.0) (2020-04-22)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.7.1...v0.8.0)

**Implemented enhancements:**

- Switch to pydantic's BaseSettings for the config file? [\#152](https://github.com/Materials-Consortia/optimade-python-tools/issues/152)
- Use services for testing/updating dependencies? [\#96](https://github.com/Materials-Consortia/optimade-python-tools/issues/96)
- Remove query constraints for /links-endpoint [\#244](https://github.com/Materials-Consortia/optimade-python-tools/pull/244) ([CasperWA](https://github.com/CasperWA))
- Add adapters - Base design + 'structures' \(+ 'references'... sort of\) [\#241](https://github.com/Materials-Consortia/optimade-python-tools/pull/241) ([CasperWA](https://github.com/CasperWA))
- Add dependabot and last commit date badges [\#237](https://github.com/Materials-Consortia/optimade-python-tools/pull/237) ([CasperWA](https://github.com/CasperWA))
- Add mongo length operator functionality with length aliases [\#222](https://github.com/Materials-Consortia/optimade-python-tools/pull/222) ([ml-evs](https://github.com/ml-evs))

**Fixed bugs:**

- Use Path.home\(\) instead of ~ in default config path values [\#245](https://github.com/Materials-Consortia/optimade-python-tools/issues/245)

**Closed issues:**

- Have Dependabot take care of various requirements.txt files as well [\#249](https://github.com/Materials-Consortia/optimade-python-tools/issues/249)
- Remove commented out GH Action job `deps\_clean-install` [\#247](https://github.com/Materials-Consortia/optimade-python-tools/issues/247)
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

## [v0.7.1](https://github.com/materials-consortia/optimade-python-tools/tree/v0.7.1) (2020-03-16)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.7.0...v0.7.1)

**Closed issues:**

- Fix all capitalisation of OPTIMADE [\#232](https://github.com/Materials-Consortia/optimade-python-tools/issues/232)
- Remove validator action from README [\#230](https://github.com/Materials-Consortia/optimade-python-tools/issues/230)

**Merged pull requests:**

- Fix github actions for non-release tags [\#235](https://github.com/Materials-Consortia/optimade-python-tools/pull/235) ([shyamd](https://github.com/shyamd))
- Update OPTIMADE capitalisation [\#233](https://github.com/Materials-Consortia/optimade-python-tools/pull/233) ([ml-evs](https://github.com/ml-evs))
- Update mentions of action in readme [\#231](https://github.com/Materials-Consortia/optimade-python-tools/pull/231) ([ml-evs](https://github.com/ml-evs))

## [v0.7.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.7.0) (2020-03-13)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.6.0...v0.7.0)

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
- Codecov-action supports token-less uploads [\#220](https://github.com/Materials-Consortia/optimade-python-tools/pull/220) ([CasperWA](https://github.com/CasperWA))
- Update django requirement from \>=2.2.9,~=2.2 to \>=2.2,\<4.0 [\#219](https://github.com/Materials-Consortia/optimade-python-tools/pull/219) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))
- Update elasticsearch-dsl requirement from ~=6.4 to \>=6.4,\<8.0 [\#218](https://github.com/Materials-Consortia/optimade-python-tools/pull/218) ([dependabot-preview[bot]](https://github.com/apps/dependabot-preview))

## [v0.6.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.6.0) (2020-03-06)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.5.0...v0.6.0)

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

## [v0.5.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.5.0) (2020-02-13)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.4.0...v0.5.0)

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

## [v0.4.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.4.0) (2020-02-06)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.3.4...v0.4.0)

**Implemented enhancements:**

- switch to pipenv? [\#37](https://github.com/Materials-Consortia/optimade-python-tools/issues/37)
- Reorder tests [\#162](https://github.com/Materials-Consortia/optimade-python-tools/pull/162) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Server app intermingles [\#161](https://github.com/Materials-Consortia/optimade-python-tools/issues/161)
- `response\_fields` not working [\#154](https://github.com/Materials-Consortia/optimade-python-tools/issues/154)

**Closed issues:**

- Change `page\_page` to `page\_number` [\#165](https://github.com/Materials-Consortia/optimade-python-tools/issues/165)
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

## [v0.3.4](https://github.com/materials-consortia/optimade-python-tools/tree/v0.3.4) (2020-02-04)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.3.3...v0.3.4)

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

## [v0.3.3](https://github.com/materials-consortia/optimade-python-tools/tree/v0.3.3) (2020-01-24)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.3.2...v0.3.3)

**Fixed bugs:**

- Lark files not being distributed [\#141](https://github.com/Materials-Consortia/optimade-python-tools/issues/141)

**Closed issues:**

- Tests fail with lark-parser\>=0.8 [\#146](https://github.com/Materials-Consortia/optimade-python-tools/issues/146)

**Merged pull requests:**

- Updated lark-parser to 0.8.1 [\#149](https://github.com/Materials-Consortia/optimade-python-tools/pull/149) ([ml-evs](https://github.com/ml-evs))
- Split eager and standard tests to avoid unnecessary badge of shame [\#148](https://github.com/Materials-Consortia/optimade-python-tools/pull/148) ([ml-evs](https://github.com/ml-evs))
- Bump to v0.3.3 [\#147](https://github.com/Materials-Consortia/optimade-python-tools/pull/147) ([CasperWA](https://github.com/CasperWA))
- Fix root\_validator issues with optional fields and made meta optional [\#145](https://github.com/Materials-Consortia/optimade-python-tools/pull/145) ([ml-evs](https://github.com/ml-evs))
- Handle `JSONDecodeError`s in validator [\#144](https://github.com/Materials-Consortia/optimade-python-tools/pull/144) ([ml-evs](https://github.com/ml-evs))

## [v0.3.2](https://github.com/materials-consortia/optimade-python-tools/tree/v0.3.2) (2020-01-20)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.3.1...v0.3.2)

**Implemented enhancements:**

- Add base URL to configuration file [\#135](https://github.com/Materials-Consortia/optimade-python-tools/pull/135) ([CasperWA](https://github.com/CasperWA))

**Fixed bugs:**

- Fix `load\_from\_json` [\#137](https://github.com/Materials-Consortia/optimade-python-tools/pull/137) ([CasperWA](https://github.com/CasperWA))

**Merged pull requests:**

- Make sure relevant package data is included in distributions [\#142](https://github.com/Materials-Consortia/optimade-python-tools/pull/142) ([CasperWA](https://github.com/CasperWA))
- Add database page limit [\#139](https://github.com/Materials-Consortia/optimade-python-tools/pull/139) ([CasperWA](https://github.com/CasperWA))

## [v0.3.1](https://github.com/materials-consortia/optimade-python-tools/tree/v0.3.1) (2020-01-17)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.3.0...v0.3.1)

**Merged pull requests:**

- Update requirements [\#138](https://github.com/Materials-Consortia/optimade-python-tools/pull/138) ([CasperWA](https://github.com/CasperWA))

## [v0.3.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.3.0) (2020-01-14)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.1.2...v0.3.0)

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
- Updates to README and docs for v0.10.0 [\#68](https://github.com/Materials-Consortia/optimade-python-tools/pull/68) ([ml-evs](https://github.com/ml-evs))
- Adding grammar for v0.10.0 [\#66](https://github.com/Materials-Consortia/optimade-python-tools/pull/66) ([fekad](https://github.com/fekad))

## [v0.1.2](https://github.com/materials-consortia/optimade-python-tools/tree/v0.1.2) (2018-06-14)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.1.1...v0.1.2)

## [v0.1.1](https://github.com/materials-consortia/optimade-python-tools/tree/v0.1.1) (2018-06-13)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/v0.1.0...v0.1.1)

## [v0.1.0](https://github.com/materials-consortia/optimade-python-tools/tree/v0.1.0) (2018-06-05)

[Full Changelog](https://github.com/materials-consortia/optimade-python-tools/compare/6680fb28a60ec4ff43a303b7b4dbf41e159a25b6...v0.1.0)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
