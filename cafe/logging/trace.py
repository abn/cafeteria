import logging

TRACE = 5
logging.addLevelName(5, 'TRACE')
logging.TRACE = 5


def trace(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'TRACE'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.trace("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)


class TraceEnabledLogger(logging.Logger):
    trace = trace


logging.Logger.trace = trace

# noinspection PyProtectedMember
LOGGING_LEVELS = logging._levelNames
