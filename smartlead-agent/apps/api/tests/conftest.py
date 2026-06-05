import os
import tempfile

import pytest

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/smartlead_agent_test.db"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_database():
    from app import models  # noqa: F401
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
