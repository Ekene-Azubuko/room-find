import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Create an application backed only by a disposable test database."""
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})


@pytest.fixture
def client(app):
    """Return an isolated HTTP client."""
    return app.test_client()
