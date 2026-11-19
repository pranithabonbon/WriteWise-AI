import mongomock
import pytest

from app import create_app
from config import TestConfig


class MongoTestConfig(TestConfig):
    # In-memory MongoDB stand-in: tests need no Atlas account or network
    MONGO_CLIENT = mongomock.MongoClient()


@pytest.fixture()
def app():
    MongoTestConfig.MONGO_CLIENT = mongomock.MongoClient()  # fresh empty DB per test
    app = create_app(MongoTestConfig)
    with app.app_context():
        from app.db import ensure_indexes, get_db

        ensure_indexes(get_db())
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()