# Cafeteria

[![PyPI version](https://img.shields.io/pypi/v/cafeteria.svg)](https://pypi.org/project/cafeteria/)
[![Python Versions](https://img.shields.io/pypi/pyversions/cafeteria.svg)](https://pypi.org/project/cafeteria/)
[![Test Suite](https://github.com/abn/cafeteria/actions/workflows/test-suite.yml/badge.svg)](https://github.com/abn/cafeteria/actions/workflows/test-suite.yml)
[![Code Quality](https://github.com/abn/cafeteria/actions/workflows/code-quality.yml/badge.svg)](https://github.com/abn/cafeteria/actions/workflows/code-quality.yml)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked: ty](https://img.shields.io/badge/types-ty-blue.svg)](https://github.com/astral-sh/ty)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Cafeteria** is a lightweight Python toolkit providing reusable building blocks, data structures, asyncio patterns, logging mixins, and design patterns for modern Python applications (3.10+).

---

## Features

- **Data Structures (`cafeteria.datastructs`)**:
  - `AttributeDict` & `DeepAttributeDict`: Access dictionary keys as object attributes with recursive nested mapping support.
  - `ReadOnlyDict`: An immutable dictionary mapping preventing modification after initialization and supporting hashing for hashable values.
  - `FrozenAttributeDict` & `DeepFrozenAttributeDict`: Immutable attribute dictionary for safe runtime configuration objects.
  - `CaseInsensitiveDict` & `DeepCaseInsensitiveDict`: Header- and key-insensitive dictionary supporting attribute and item lookups with casing preservation.
  - `MergingDict` & `DeepMergingDict`: Dictionaries that automatically merge nested dictionaries, lists, or update-compatible values on attribute or key assignment.
  - `BorgDict`: A dictionary backed directly by shared Borg singleton state.
  - `JSONAttributeDict`: Attribute dictionary with seamless JSON serialization and pretty-printing.
  - `Memory` & `MemoryUnit`: Human-readable memory unit parsing, conversion, and arithmetic (`Memory("1024 KB")`, `MemoryUnit.GB`).
  - `Duration` & `TimeUnit`: Human-readable time duration parsing, unit conversions, and `timedelta` arithmetic (`Duration("1h 30m 15s")`, `Duration(90, TimeUnit.MINUTES)`).
  - `DataUnit` & `DataRateUnit`: Bit/byte and bandwidth rate conversion utilities (`DataUnit(1, "byte").bit == 8`, `DataRateUnit(100, "Mbps")`).
- **AsyncIO Utilities & Patterns (`cafeteria.asyncio`)**:
  - `PeriodicTask` & `AsyncTimer`: Recurring coroutine runner with monotonic drift compensation, pause/resume/stop controls, error hooks, and `cancel_all_tasks` integration.
  - `Callback` & `CallbackRegistry`: Synchronous and asynchronous event dispatching and handler registries.
  - `cancel_all_tasks` & `cancel_tasks_on_termination`: Graceful event loop shutdown and signal cancellation (SIGINT, SIGTERM).
  - `AsyncioGracefulApplication`: Standard lifecycle pattern for asyncio applications with signal trapping and task cleanup.
- **Design Patterns (`cafeteria.patterns`)**:
  - `Borg` & `BorgStateManager`: Pythonic Borg singleton pattern supporting isolated state across subclasses.
  - `SessionManager`: Generic, reusable context manager protocol for session lifecycle management.
  - `get_by_path`: Safe, deep key path traversal for nested mappings (`get_by_path(d, "a", "b", "c", default=None)`).
  - `ContextMixin`: Lightweight context manager base mixin.
- **Logging Mixins & Tools (`cafeteria.logging`)**:
  - `LoggedObject`: Mixin injecting a context-aware `.logger` with `TRACE` level and enter/exit trace logging.
  - `TRACE` logging level (`logging.TRACE = 5`).
  - `LoggingManager`: Declarative logging configuration management from YAML files or environment variables.
- **Decorators (`cafeteria.decorators`)**:
  - `retry`: Zero-dependency retry decorator supporting both sync and async functions with exponential backoff, jitter, selective exception catching, and hooks.
  - `classproperty`: Class-level read-only property decorator compatible across Python 3.10–3.14.
- **General Utilities (`cafeteria.utilities`)**:
  - `listify`: Coerce arguments, tuples, or sets into standard Python lists.
  - `resolve_setting`: Hierarchical configuration resolution (CLI argument > Environment Variable > Config File > Default).
  - `to_bool` & `boolify`: Safe string-to-boolean coercion (`"true"`, `"yes"`, `"1"`, `"on"` -> `True`) with default fallback support.

---

## Installation

Install Cafeteria from PyPI:

```bash
pip install cafeteria
```

With optional YAML logging configuration support:

```bash
pip install "cafeteria[yaml]"
```

Using Poetry:

```bash
poetry add cafeteria
```

---

## Quickstart & Examples

### 1. Attribute and Merging Dictionaries

```python
from cafeteria.datastructs import (
    AttributeDict,
    CaseInsensitiveDict,
    DeepFrozenAttributeDict,
    DeepMergingDict,
    FrozenAttributeDict,
    ReadOnlyDict,
)

# Access keys as attributes
cfg = AttributeDict({"server": {"host": "localhost", "port": 8080}})
assert cfg.server["host"] == "localhost"

# Immutable configuration objects
frozen_cfg = DeepFrozenAttributeDict({"database": {"host": "localhost", "port": 5432}})
assert frozen_cfg.database.host == "localhost"
# frozen_cfg.database.host = "remote"  # Raises AttributeError!

# Header- and case-insensitive dictionaries with attribute and key lookup
headers = CaseInsensitiveDict({"Content-Type": "application/json", "Host": "example.com"})
assert headers["content-type"] == "application/json"
assert headers.content_type == "application/json"
assert headers.Host == "example.com"
headers.content_type = "text/html"
assert headers["Content-Type"] == "text/html"

# Automatically merge nested data structures
merged = DeepMergingDict({"tags": ["python"], "database": {"port": 5432}})
merged.tags = ["asyncio"]
merged.database = {"host": "db.local"}

# Lists are extended and dicts are recursively merged:
assert merged.tags == ["python", "asyncio"]
assert merged.database.host == "db.local"
assert merged.database.port == 5432
```

### 2. Memory, Time, and Data Units

```python
from cafeteria.datastructs import Duration, Memory, MemoryUnit, TimeUnit
from cafeteria.datastructs.units.data import DataRateUnit, DataUnit

# Parse and convert time durations
d = Duration("1h 30m 15s")
assert d.total_seconds == 5415.0
assert d == Duration(90, TimeUnit.MINUTES) + Duration(15, TimeUnit.SECONDS)
assert d.hours == 1.5041666666666667
assert d.seconds == 5415

# Parse and convert memory sizes
ram = Memory("1024 KB")
assert ram == 1024 * 1024
assert ram == Memory(1, MemoryUnit.MB)

# Bit and byte conversions
size = DataUnit(1, "byte")
assert size == 8  # 8 bits
assert size.byte == 1  # 1 byte
assert size.bit == 8

# Data bandwidth rates
rate = DataRateUnit(100, "Mbps")
assert rate == 100 * 10**6  # 100,000,000 bits per second
```

### 3. AsyncIO Callback Dispatcher & Graceful Shutdown

```python
import asyncio
from cafeteria.asyncio import CallbackRegistry, cancel_tasks_on_termination

registry = CallbackRegistry()


# Register synchronous or coroutine callbacks
@registry.register("on_startup")
async def startup_handler(app_name: str):
    print(f"Starting {app_name}...")


async def main():
    loop = asyncio.get_running_loop()
    # Register SIGINT / SIGTERM graceful shutdown handlers
    cancel_tasks_on_termination(loop)

    # Dispatch events
    registry.dispatch("on_startup", "MyApp")


asyncio.run(main())
```

### 4. Periodic Tasks & Async Timer

```python
import asyncio
from cafeteria.asyncio import periodic_task, PeriodicTask
from cafeteria.datastructs import Duration


# Decorate a coroutine with drift compensation
@periodic_task(interval=Duration("5s"), immediate=True)
async def heartbeat():
    print("Heartbeat ping...")


async def main():
    # Context manager automatically starts and stops the task
    async with heartbeat:
        await asyncio.sleep(12)
        heartbeat.pause()
        await asyncio.sleep(5)
        heartbeat.resume()

    # Direct instantiation with error handling
    def on_error(exc: Exception):
        print(f"Task error: {exc}")

    runner = PeriodicTask(heartbeat.tick, interval=1.0, on_error=on_error)
    runner.start()
    await asyncio.sleep(3)
    runner.stop()


asyncio.run(main())
```

### 5. Borg Singleton Pattern

```python
from cafeteria.patterns import Borg


class DatabasePool(Borg):
    pass


class CachePool(Borg):
    pass


db1 = DatabasePool()
db1.connection = "postgresql://localhost:5432"

db2 = DatabasePool()
assert db2.connection == "postgresql://localhost:5432"

# Child subclasses maintain isolated state from other Borg classes
cache = CachePool()
assert not hasattr(cache, "connection")
```

### 6. Context-Aware Logging & Trace Level

```python
from cafeteria.logging import LoggedObject, LoggingManager

# Enable TRACE logging level
LoggingManager.set_level("TRACE")


class Worker(LoggedObject):
    def process(self):
        self.logger.trace("Processing worker job")


with Worker() as worker:
    worker.process()
```

### 7. Deep Key Traversal (`get_by_path`)

```python
from cafeteria.patterns import get_by_path

data = {"services": {"auth": {"jwt": {"secret": "supersecret"}}}}

secret = get_by_path(data, "services", "auth", "jwt", "secret")
assert secret == "supersecret"

missing = get_by_path(data, "services", "database", "host", default="localhost")
assert missing == "localhost"
```

### 8. Sync and Async Retry Decorator

```python
import asyncio
from cafeteria.datastructs import Duration
from cafeteria.decorators import retry


# Asynchronous function with exponential backoff, jitter, and selective retry
@retry(
    attempts=3,
    backoff=0.5,
    factor=2.0,
    jitter=True,
    retry_on=(ConnectionError, TimeoutError),
)
async def fetch_data(url: str) -> str:
    # Retries up to 3 times on ConnectionError or TimeoutError
    return "response"


# Synchronous function with Duration support and retry callback
def log_retry(exc: Exception, attempt: int, delay: float) -> None:
    print(f"Attempt {attempt} failed with {exc}. Retrying in {delay:.2f}s...")


@retry(
    attempts=4,
    backoff=Duration("250ms"),
    max_backoff=Duration("2s"),
    on_retry=log_retry,
)
def compute() -> int:
    return 42
```

### 9. Safe Boolean Coercion (`to_bool` / `boolify`)

```python
from cafeteria.utilities import boolify, to_bool

# Coerce truthy representations
assert to_bool("true") is True
assert to_bool("yes") is True
assert to_bool("1") is True
assert to_bool("on") is True
assert to_bool("enabled") is True

# Coerce falsy representations
assert to_bool("false") is False
assert to_bool("no") is False
assert to_bool("0") is False
assert to_bool("off") is False
assert to_bool("disabled") is False

# Safe fallback with default
assert to_bool("unknown", default=False) is False
assert boolify("invalid", default=True) is True
```

---

## Development

Cafeteria uses [Poetry](https://python-poetry.org/) for packaging and dependency management, [Ruff](https://astral.sh/ruff) for linting and formatting, [Astral `ty`](https://astral.sh/ty) for static type checking, and [pytest](https://pytest.org/) for testing.

### Setup

```bash
git clone https://github.com/abn/cafeteria.git
cd cafeteria
poetry install
poetry run pre-commit install
```

### Running Tests & Quality Checks

```bash
# Run pytest with code coverage
poetry run pytest

# Run Ruff linter and formatter checks
ruff check src/ tests/
ruff format --check src/ tests/

# Run static type checking with ty
ty check src/ tests/

# Run pre-commit hooks on all files
poetry run pre-commit run --all-files

# Build distribution wheels and sdist
poetry build
```

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
