from functools import wraps

from sqlalchemy.orm import sessionmaker

from cafe.abc.compat import abstractclassmethod
from cafe.patterns.context import SessionManager


class SQLAlchemySessionManager(SessionManager):
    ENGINE = None

    @classmethod
    def default(cls):
        return cls.instance()

    @classmethod
    def instance(cls, engine=None):
        """
        :type engine: sqlalchemy.engine.Engine or None
        :rtype: cafe.database.sqlalchemy.session.SQLAlchemySessionManager
        """
        return cls(cls.factory(engine))

    @classmethod
    def factory(cls, engine=None):
        if engine is None:
            engine = cls.engine()
        return sessionmaker(bind=engine)

    @classmethod
    def engine(cls):
        if cls.ENGINE is None:
            cls.ENGINE = cls.get_engine()
        return cls.ENGINE

    @abstractclassmethod
    def get_engine(cls, *args, **kwargs):
        """
        Default engine for this session manager.

        :rtype: sqlalchemy.engine.Engine
        """
        raise NotImplementedError

    def __enter__(self):
        """
        :rtype: sqlalchemy.orm.session.Session
        """
        return super(SQLAlchemySessionManager, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        rvalue = True
        if exc_type is not None:
            self.session.rollback()
            rvalue = False
        else:
            self.session.commit()
        super(SQLAlchemySessionManager, self).__exit__(exc_type, exc_val, exc_tb)
        return rvalue


def sessioned_query(session_manager=None, engine=None, context=False):
    """
    Decorator which wraps a function in a SQLAlchemy session

    :param context: execute the wrapped function inside a session context
    :type context: bool
    :param session_manager: SessionManager to use
    :type session_manager: cafe.database.sqlalchemy.session.SQLAlchemySessionManager
    :param engine: Engine to use to connect to Mimir
    :type engine: sqlalchemy.engine.Engine
    """
    session_keyword_arg = 'session'

    def session_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            execute_in_context = context
            if session_keyword_arg not in kwargs or kwargs[session_keyword_arg] is None:
                if session_manager is None:
                    raise TypeError(
                        'sessioned query functions should be called with an SQLAlchemySessionManager '
                        'or Session instance when a default session manager is not configured.')
                kwargs[session_keyword_arg] = session_manager.instance(engine=engine)
                execute_in_context = True

            instance = kwargs.pop(session_keyword_arg)

            if isinstance(instance, SQLAlchemySessionManager):
                instance = instance.instance(engine=engine)
                execute_in_context = True

            if execute_in_context:
                with instance as session:
                    return function(*args, session=session, **kwargs)
            else:
                return function(*args, session=instance, **kwargs)

        return wrapper

    return session_decorator
