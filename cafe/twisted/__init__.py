
try:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    from twisted.internet import defer, reactor

    def async_sleep(seconds):
        """
        An asynchronous sleep function using twsited.

        Source: http://twistedmatrix.com/pipermail/twisted-python/2009-October/020788.html # noqa

        :type seconds: int
        """
        d = defer.Deferred()
        # noinspection PyUnresolvedReferences
        reactor.callLater(seconds, d.callback, seconds)
        return d
except ImportError:
    pass
