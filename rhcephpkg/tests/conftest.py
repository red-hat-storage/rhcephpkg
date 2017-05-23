import os
import pytest


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, 'fixtures')


@pytest.fixture(autouse=True)
def fake_home(monkeypatch):
    monkeypatch.setenv('HOME', FIXTURES_DIR)
