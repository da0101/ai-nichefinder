from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from nichefinder_core.settings import Settings


def get_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session_factory(settings: Settings) -> sessionmaker:
    return sessionmaker(bind=get_engine(settings), autoflush=False, autocommit=False)

