from nichefinder_core.settings import Settings

from nichefinder_db.base import Base
from nichefinder_db.session import get_engine

# Import models so metadata is registered before bootstrap.
from nichefinder_db import models as _models  # noqa: F401


def create_schema(settings: Settings) -> None:
    engine = get_engine(settings)
    Base.metadata.create_all(bind=engine)

