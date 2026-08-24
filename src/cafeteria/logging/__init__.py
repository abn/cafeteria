from __future__ import annotations

import logging
import logging.config
from os import getenv
from os.path import isfile
from types import TracebackType
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar
from typing import cast

from cafeteria.logging.trace import LOGGING_LEVELS
from cafeteria.patterns.mixins import ContextMixin

if TYPE_CHECKING:
    from cafeteria.logging.trace import TraceEnabledLogger

__all__ = ["LoggedObject", "LoggingManager"]


class LoggingManager:
    CONFIGFILE_ENV_KEY = "LOG_CFG"

    @classmethod
    def set_level(cls, level: int | str) -> None:
        """
        :raises: ValueError
        """
        lvl = level if not isinstance(level, str) else int(LOGGING_LEVELS.get(level.upper(), level))

        for handler in logging.root.handlers:
            handler.setLevel(lvl)

        logging.root.setLevel(lvl)

    @classmethod
    def load_config(cls, configfile: str | None = None) -> None:
        """
        :raises: ValueError
        """
        configfile = configfile or getenv(cls.CONFIGFILE_ENV_KEY, "logging.yaml")

        if isfile(configfile):
            try:
                import yaml
            except ImportError:
                raise Warning(
                    f"Loading logging configuration file {configfile} requires PyYAML to be available in your runtime "
                    f"environment. Skipping configuration."
                ) from None
            else:
                with open(configfile) as cf:
                    # noinspection PyBroadException
                    try:
                        logging.config.dictConfig(yaml.safe_load(cf))
                    except ValueError:
                        logging.debug("Learn to config foooo! Improper config at %s", configfile)
                    except Exception:
                        logging.exception("Something went wrong while reading %s.", configfile)
        else:
            raise ValueError(f"Invalid configfile specified: {configfile}")


T = TypeVar("T", bound="LoggedObject")


# noinspection PyPep8Naming
class LoggedObject(ContextMixin):
    logger: TraceEnabledLogger

    def __new__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        cls.logger = cast(
            "TraceEnabledLogger",
            logging.getLogger(f"{cls.__module__}.{cls.__name__}"),
        )
        cls.logger.trace("Instantiating %s.%s", cls.__module__, cls.__qualname__)
        return super().__new__(cls)

    def __enter__(self: T) -> T:
        self.logger.trace(
            "Entering context for %s.%s", self.__module__, self.__class__.__qualname__
        )
        return super().__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.logger.trace("Exiting context for %s.%s", self.__module__, self.__class__.__qualname__)
        super().__exit__(exc_type, exc_val, exc_tb)
