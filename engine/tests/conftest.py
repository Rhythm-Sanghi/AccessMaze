from pathlib import Path

import pytest

from accessmaze.fixtures import FixtureServer
from accessmaze.models import ProjectInput
from accessmaze.storage import Store
from accessmaze.templates import template


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


@pytest.fixture(scope="session")
def fixtures():
    server = FixtureServer()
    yield server
    server.close()


@pytest.fixture
def project(store):
    def create(kind="accessible"):
        return store.save_project(ProjectInput(name=kind, journey=template(kind)))

    return create


@pytest.fixture
def axe_path():
    return Path(__file__).resolve().parents[2] / "node_modules/axe-core/axe.min.js"
