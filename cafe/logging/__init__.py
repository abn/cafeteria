from logging import getLogger, debug, exception, root
from logging.config import dictConfig

from os import getenv
from os.path import isfile
from yaml import safe_load as load

from cafe.logging.trace import LOGGING_LEVELS
from cafe.patterns.mixins import ContextMixin
from cafe.utilities import is_str


class LoggingManager(object):
    CONFIGFILE_ENV_KEY = 'LOG_CFG'

    @classmethod
    def set_level(cls, level):
        """
        :raises: ValueError
        """
        level = level \
            if not is_str(level) \
            else int(LOGGING_LEVELS.get(level.upper(), level))

        for handler in root.handlers:
            handler.setLevel(level)

        root.setLevel(level)

    @classmethod
    def load_config(cls, configfile='logging.yaml'):
        """
        :raises: ValueError
        """
        configfile = getenv(cls.CONFIGFILE_ENV_KEY, configfile)
        if isfile(configfile):
            with open(configfile, 'r') as cf:
                # noinspection PyBroadException
                try:
                    dictConfig(load(cf))
                except ValueError:
                    debug(
                        'Learn to config foooo! Improper config at %s',
                        configfile
                    )
                except Exception:
                    exception(
                        'Something went wrong while reading %s.',
                        configfile
                    )
        else:
            raise ValueError(
                'Invalid configfile specified: {}'.format(configfile)
            )


# noinspection PyPep8Naming
class LoggedObject(ContextMixin):
    def __new__(cls, *args, **kwargs):
        cls.logger = getLogger('{}.{}'.format(cls.__module__, cls.__name__))
        """:type: cafe.logging.trace.TraceEnabledLogger"""
        cls.logger.trace('Instantiating')
        return super(LoggedObject, cls).__new__(cls)

    def __enter__(self):
        self.logger.trace('Entering')
        return super(LoggedObject, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.trace('Exiting')
        super(LoggedObject, self).__exit__(exc_type, exc_val, exc_tb)
