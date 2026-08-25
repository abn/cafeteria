# Changelog

## [1.1.0](https://github.com/abn/cafeteria/compare/v1.0.0...v1.1.0) (2026-08-25)


### Features

* **asyncio:** add PeriodicTask and AsyncTimer runner ([#192](https://github.com/abn/cafeteria/issues/192)) ([9cfa567](https://github.com/abn/cafeteria/commit/9cfa56760614b0685306bc1d8daa5a0993aecf4a))
* **datastructs:** add ReadOnlyDict, FrozenAttributeDict, and CaseInsensitiveDict ([#191](https://github.com/abn/cafeteria/issues/191)) ([84d9b64](https://github.com/abn/cafeteria/commit/84d9b6408958d5da17f99cd64fdd0cb1077aa9df))
* **decorators:** add zero-dependency retry decorator ([#189](https://github.com/abn/cafeteria/issues/189)) ([dba6dbf](https://github.com/abn/cafeteria/commit/dba6dbfe0b8312c19aa499569341758568469e23))
* **units:** add Duration and TimeUnit classes ([#188](https://github.com/abn/cafeteria/issues/188)) ([5e79c4b](https://github.com/abn/cafeteria/commit/5e79c4b745d1b2481f9afee5cf072f11cfbcc354))
* **utilities:** add to_bool and boolify ([#190](https://github.com/abn/cafeteria/issues/190)) ([9a5316e](https://github.com/abn/cafeteria/commit/9a5316e93c949f3c402d0aed234fcca91e61c95b))


### Build & Packaging

* **deps:** bump the github-actions group with 2 updates ([#187](https://github.com/abn/cafeteria/issues/187)) ([593d659](https://github.com/abn/cafeteria/commit/593d659a3809f0a7e9dce4bf7be0d33cf83a7f5f))


### Continuous Integration

* configure monthly grouped dependabot updates ([dd66ffd](https://github.com/abn/cafeteria/commit/dd66ffda743a262451e0279a180d80b578e20b81))

## [1.0.0](https://github.com/abn/cafeteria/compare/v0.22.3...v1.0.0) (2026-08-25)


### Features

* **asyncio:** import and modernize subpackage ([c5a814d](https://github.com/abn/cafeteria/commit/c5a814d5b874cb21c6a5ffdb456a8778ec336dba))


### Refactoring

* **abc:** drop superseded AbstractClass ([973fcc1](https://github.com/abn/cafeteria/commit/973fcc1ac74c8dd689b6bedc93a3e4f479c3f533))
* **asyncio:** drop deprecated shims ([41c0403](https://github.com/abn/cafeteria/commit/41c0403206fb912d8b73420875acc74772a1b974))
* **asyncio:** drop execute_async_method ([ddcb4e3](https://github.com/abn/cafeteria/commit/ddcb4e311b29cc83ac861219fd62ca7504af3d66))
* drop legacy empty compat modules ([c8eaf89](https://github.com/abn/cafeteria/commit/c8eaf8954d466832da6ed6a45e273698ef41dcc1))
* drop obsolete twisted subpackage ([98c0202](https://github.com/abn/cafeteria/commit/98c02023c910012e638e5c960e479260edb1cf5a))
* drop sonarcloud configuration ([b3d1fe3](https://github.com/abn/cafeteria/commit/b3d1fe3f1112c7defa3363163fed1e856a7bbfc9))
* modernize core building blocks and exports ([d841d35](https://github.com/abn/cafeteria/commit/d841d35a2e7a04c896eb5d7c06a11ba826193b54))
* modernize syntax and add types for ty ([28cb2ab](https://github.com/abn/cafeteria/commit/28cb2abb7cc056ecc0e68f40f58e0c2040945431))


### Documentation

* add comprehensive markdown readme ([1a36ec7](https://github.com/abn/cafeteria/commit/1a36ec7899e66f581355f3f8fcefffa2f0e0ba6e))


### Build & Packaging

* add Ruff and Astral ty configuration ([ef03376](https://github.com/abn/cafeteria/commit/ef03376f25fa3b8922698e323f9e7095a550528e))
* bump dev dependencies and pre-commit hooks ([5fc93ec](https://github.com/abn/cafeteria/commit/5fc93ecde33ad0635fd5b7b66858e6d2cfd47eee))
* **deps-dev:** bump coverage from 4.5.3 to 4.5.4 ([#14](https://github.com/abn/cafeteria/issues/14)) ([2ba24b4](https://github.com/abn/cafeteria/commit/2ba24b469b947605ba5e1390700ec65b6845b322))
* **deps-dev:** bump pre-commit from 1.17.0 to 1.18.0 ([#16](https://github.com/abn/cafeteria/issues/16)) ([ac59d4d](https://github.com/abn/cafeteria/commit/ac59d4d202ecec7a7551d35dd6d8225007fb4b51))
* **deps:** [security] bump py from 1.9.0 to 1.10.0 ([ecace26](https://github.com/abn/cafeteria/commit/ecace268a5e81878f0708817c9b1b40ff1cebd07))
* **deps:** [security] bump pyyaml from 3.13 to 5.1 ([#4](https://github.com/abn/cafeteria/issues/4)) ([392e030](https://github.com/abn/cafeteria/commit/392e030ded3884cd87be5634798697c8162aa8d6))
* **deps:** bump pyyaml from 5.1.1 to 5.1.2 ([c44dfb3](https://github.com/abn/cafeteria/commit/c44dfb3cbe8afe0ad94730925cb6dbac441a7443))
* **deps:** bump pyyaml from 5.1.2 to 5.2 ([75f62e9](https://github.com/abn/cafeteria/commit/75f62e948318156086b41b9f80851f57539bb9e1))
* **deps:** bump pyyaml from 5.3 to 5.3.1 ([f2df487](https://github.com/abn/cafeteria/commit/f2df4875709c06e8e5846b7f06455e89cf377611))
* **deps:** bump six from 1.12.0 to 1.13.0 ([0052308](https://github.com/abn/cafeteria/commit/0052308552c8fc3a926c7848204f86bd00596707))
* ignore uv.lock and configure ty pre-commit ([1f03a9c](https://github.com/abn/cafeteria/commit/1f03a9c0783ad50c7caf72d356b484791453b6c9))
* modernize pyproject.toml to PEP 621 format ([0a425b3](https://github.com/abn/cafeteria/commit/0a425b3e77375955d5744799cacda4db1667c800))


### Continuous Integration

* fix action versions ([d3ed00d](https://github.com/abn/cafeteria/commit/d3ed00d5158ec184157c3558470c3f32054bbe30))
* fix branch names ([3621ef4](https://github.com/abn/cafeteria/commit/3621ef42a6ddc5a5fed1d28e4ac94c5ac565504c))
* fix poetry installation and handle python version 3.10 ([b783ac9](https://github.com/abn/cafeteria/commit/b783ac9b66a84e964cbc6bd0e27f8454dcdaa11b))
* fix pre-commit action version ([bc78503](https://github.com/abn/cafeteria/commit/bc7850349557258f1670611dd30a6726c8ac23bf))
* integrate release-please and prepare release 1.0.0 ([188af98](https://github.com/abn/cafeteria/commit/188af982b1998170611d5a37b8358fe7c4c92ceb))
* make a release on tag ([6214135](https://github.com/abn/cafeteria/commit/62141356b0c4b5e3c8e8b7cad48ee13a2a9ad96d))
* modernize workflows and use trusted publishing ([355f355](https://github.com/abn/cafeteria/commit/355f355e14a14662bdc7450f82170caea9d1780f))
* remove non-portable venv arg from ty hook ([92cf2ca](https://github.com/abn/cafeteria/commit/92cf2ca35f2083e9623cd60f2756235b234989a9))
* run workflows on all branches ([ddf83c3](https://github.com/abn/cafeteria/commit/ddf83c32840292cb7b3812c85ae1f651e2879786))
* update action versions to v2 ([54da6e8](https://github.com/abn/cafeteria/commit/54da6e83de71aade524b651c75f7b7840c50f0eb))
* update python versions ([d8394a3](https://github.com/abn/cafeteria/commit/d8394a3262a6f99139d6d69d6a21f63cca2c1d38))
* update workflows ([7180591](https://github.com/abn/cafeteria/commit/71805917c4f7e3cfae9b3a3567db5e8ca831516e))
* update workflows for Python 3.10-3.14 matrix ([1e62b15](https://github.com/abn/cafeteria/commit/1e62b15d1473a84a0f886f2e56727cbce88f4bec))
* use poetry pre-release ([79f74a1](https://github.com/abn/cafeteria/commit/79f74a1b31b38141cb7a62bddf677f8296aaa286))


### Miscellaneous Chores

* align pyproject version with 0.22.3 baseline ([9672664](https://github.com/abn/cafeteria/commit/96726644fa86441b37d354c588699e7e20cbd811))
* set manifest baseline to 0.22.3 ([26293dc](https://github.com/abn/cafeteria/commit/26293dc18f9773056c5aab62d13ea6895df195df))

## Changelog
