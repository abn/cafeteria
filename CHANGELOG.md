# Changelog

## [1.0.0](https://github.com/abn/cafeteria/compare/v0.22.3...v1.0.0) (2026-08-25)

### ⚠ BREAKING CHANGES

* **abc:** drop superseded `AbstractClass` ([973fcc1](https://github.com/abn/cafeteria/commit/973fcc1))
* **asyncio:** drop `execute_async_method` ([ddcb4e3](https://github.com/abn/cafeteria/commit/ddcb4e3)) and legacy compatibility shims ([41c0403](https://github.com/abn/cafeteria/commit/41c0403))
* drop obsolete `twisted` subpackage ([98c0202](https://github.com/abn/cafeteria/commit/98c0202)) and empty compatibility modules ([c8eaf89](https://github.com/abn/cafeteria/commit/c8eaf89))
* drop support for Python < 3.10; require Python `>= 3.10` ([0a425b3](https://github.com/abn/cafeteria/commit/0a425b3))

### Features

* **asyncio:** import and modernize subpackage with `Callback`, `CallbackRegistry`, `SimpleTriggerCallback`, `trigger_callback`, `cancel_all_tasks`, and `cancel_tasks_on_termination` ([c5a814d](https://github.com/abn/cafeteria/commit/c5a814d))

### Refactoring

* modernize core building blocks, module layout, and public exports ([d841d35](https://github.com/abn/cafeteria/commit/d841d35))
* modernize Python syntax with modern typing and annotations for Astral `ty` ([28cb2ab](https://github.com/abn/cafeteria/commit/28cb2ab))
* drop SonarCloud configuration ([b3d1fe3](https://github.com/abn/cafeteria/commit/b3d1fe3))

### Documentation

* add comprehensive markdown README with usage examples and API documentation ([1a36ec7](https://github.com/abn/cafeteria/commit/1a36ec7))

### Build & Packaging

* modernize `pyproject.toml` to PEP 621 format and Poetry 2.0 specs ([0a425b3](https://github.com/abn/cafeteria/commit/0a425b3))
* add Ruff and Astral `ty` configuration ([ef03376](https://github.com/abn/cafeteria/commit/ef03376))
* ignore `uv.lock` and configure `ty` pre-commit hook ([1f03a9c](https://github.com/abn/cafeteria/commit/1f03a9c))
* bump dev dependencies and pre-commit hooks ([5fc93ec](https://github.com/abn/cafeteria/commit/5fc93ec))
* integrate `release-please` automation retroactively
* drop redundant `__version__` from package root in favor of `pyproject.toml`

### Continuous Integration

* update test suite workflow for Python 3.10–3.14 matrix ([1e62b15](https://github.com/abn/cafeteria/commit/1e62b15))
* modernize workflows and configure PyPI Trusted Publishing ([355f355](https://github.com/abn/cafeteria/commit/355f355))
* remove non-portable venv argument from `ty` pre-commit hook ([92cf2ca](https://github.com/abn/cafeteria/commit/92cf2ca))
