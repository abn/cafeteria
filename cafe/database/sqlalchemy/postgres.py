from sqlalchemy import create_engine

from cafe.utilities import resolve_setting


def get_engine(username=None, password=None,
               host=None, port=None, database=None, env_prefix=None, **kwargs):
    """
    :type username: str
    :type password: str
    :type host: str
    :type port: int
    :type database: str
    :type env_prefix: str
    :rtype: sqlalchemy.engine.Engine
    """
    env_prefix = 'POSTGRES' if env_prefix is None else env_prefix

    username = resolve_setting('postgres', arg_value=username, env_var='{}_USERNAME'.format(env_prefix))
    password = resolve_setting(None, arg_value=password, env_var='{}_PASSWORD'.format(env_prefix))
    host = resolve_setting('localhost', arg_value=host, env_var='{}_HOST'.format(env_prefix))
    port = resolve_setting(5432, arg_value=port, env_var='{}_PORT'.format(env_prefix))
    database = resolve_setting('postgres', arg_value=database, env_var='{}_DB'.format(env_prefix))

    if password is None:
        host = ''
    else:
        host = '{username}:{password}@{host}:{port}'.format(
            username=username,
            password=password,
            host=host,
            port=port
        )

    engine = create_engine(
        'postgresql+psycopg2://{host}/{database}'.format(
            host=host,
            database=database
        ),
        **kwargs
    )
    return engine
