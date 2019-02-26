class SessionManager(object):
    def __init__(self, factory, *args, **kwargs):
        self._kwargs = kwargs
        self._args = args
        self._factory = factory
        self.session = None

    def open(self):
        if self.session is None:
            self.session = self._factory(*self._args, **self._kwargs)

    def close(self):
        if self.session is not None:
            self.session.close()
        self.session = None

    def __enter__(self):
        self.open()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
