import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# Safety guard: never run tests against the real database.
assert TEST_DATABASE_URL != os.environ["DATABASE_URL"], "Tests must not use the real database"
assert TEST_DATABASE_URL.endswith("_test"), "Test database name must end with _test"

import models  # noqa: E402,F401  (registers the tables with Base)
from database import Base  # noqa: E402
from main import app, get_db  # noqa: E402

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    def make(email: str, password: str = "correct-horse-1") -> dict:
        client.post("/users", json={"email": email, "password": password})
        response = client.post("/login", data={"username": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return make