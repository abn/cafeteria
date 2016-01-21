from six import PY2

if PY2:
    class abstractclassmethod(classmethod):

        __isabstractmethod__ = True

        def __init__(self, callable):
            callable.__isabstractmethod__ = True
            super(abstractclassmethod, self).__init__(callable)
else:
    from abc import abstractclassmethod
