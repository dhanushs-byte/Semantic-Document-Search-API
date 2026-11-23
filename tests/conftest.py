
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import main
import auth

from fastapi.testclient import TestClient


TEST_API_KEY = "test_api_key_123"


class FakeSearchEngine:

    def __init__(self, model_name, data_path):
        self.documents = []

    def refresh(self):
        pass

    def get_documents(self):
        return []

    def search(self, query, top_k=5, **kwargs):
        return [
            {
                "source": "demo.txt",
                "page": 1,
                "section": "Demo",
                "score": 0.9,
                "text": "Demo search result"
            }
        ][:top_k]


@pytest.fixture
def client(monkeypatch, tmp_path):

    # Set API key specifically for testing
    monkeypatch.setattr(
        auth,
        "API_KEY",
        TEST_API_KEY
    )

    monkeypatch.setattr(
        main,
        "SemanticSearch",
        FakeSearchEngine
    )

    monkeypatch.setattr(
        main,
        "DATA_DIR",
        tmp_path / "data"
    )

    monkeypatch.setattr(
        main,
        "DATA_PATH",
        tmp_path / "data" / "chunks.jsonl"
    )

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def headers():
    return {
        "x-api-key": TEST_API_KEY
    }
