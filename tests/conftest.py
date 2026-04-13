import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app as flask_app
import db
import tests.db_test as test_db_module


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app._tables_created = False

    with flask_app.app_context():
        test_db_module.reset_test_db()
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
