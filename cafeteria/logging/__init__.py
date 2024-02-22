from logging import debug, exception, getLogger, root
from logging.config import dictConfig
from os import getenv
from os.path import isfile

from yaml import safe_load as load

from cafeteria.logging.trace import LOGGING_LEVELS
from cafeteria.patterns.mixins import ContextMixin


class LoggingManager(object):
    CONFIGFILE_ENV_KEY = "LOG_CFG"

    @classmethod
    def set_level(cls, level):
        """
        :raises: ValueError
        """
        level = (
            level
            if not isinstance(level, str)
            else int(LOGGING_LEVELS.get(level.upper(), level))
        )

        for handler in root.handlers:
            handler.setLevel(level)

        root.setLevel(level)

    @classmethod
    def load_config(cls, configfile="logging.yaml"):
        """
        :raises: ValueError
        """
        configfile = getenv(cls.CONFIGFILE_ENV_KEY, configfile)
        if isfile(configfile):
            raise DeprecationWarning(
                "The use of a configuration file in cafeteria>=0.23.0 will required PyYAML to be explicitly installed "
                "in your runtime environment. Alternatively, you can use cafeteria[yaml] in your dependency list."
            )

            with open(configfile, "r") as cf:
                # noinspection PyBroadException
                try:
                    dictConfig(load(cf))
                except ValueError:
                    debug("Learn to config foooo! Improper config at %s", configfile)
                except Exception:
                    exception("Something went wrong while reading %s.", configfile)
        else:
            raise ValueError("Invalid configfile specified: {}".format(configfile))


# noinspection PyPep8Naming
class LoggedObject(ContextMixin):
    def __new__(cls, *args, **kwargs):
        cls.logger = getLogger("{}.{}".format(cls.__module__, cls.__name__))
        """:type: cafeteria.logging.trace.TraceEnabledLogger"""
        cls.logger.trace("Instantiating %s.%s", cls.__module__, cls.__qualname__)
        return super(LoggedObject, cls).__new__(cls)

    def __enter__(self):
        self.logger.trace(
            "Entering context for %s.%s", self.__module__, self.__class__.__qualname__
        )
        return super(LoggedObject, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.trace(
            "Exiting context for %s.%s", self.__module__, self.__class__.__qualname__
        )
        super(LoggedObject, self).__exit__(exc_type, exc_val, exc_tb)
