
def test_health(client):

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_search(client, headers):

    response = client.post(
        "/search",
        headers=headers,
        json={
            "query": "demo search",
            "top_k": 5
        }
    )

    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_invalid_top_k(client, headers):

    response = client.post(
        "/search",
        headers=headers,
        json={
            "query": "demo search",
            "top_k": 25
        }
    )

    assert response.status_code == 422


def test_missing_api_key(client):

    response = client.get("/documents")

    assert response.status_code == 401


def test_upload_document(client, headers):

    response = client.post(
        "/documents",
        headers=headers,
        files={
            "file": (
                "test.txt",
                b"This is a sample document for testing.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 200
    assert response.json()["total_chunks"] >= 1


def test_delete_document(client, headers):

    client.post(
        "/documents",
        headers=headers,
        files={
            "file": (
                "delete_me.txt",
                b"This document will be deleted.",
                "text/plain"
            )
        }
    )

    response = client.delete(
        "/documents/delete_me.txt",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["source"] == "delete_me.txt"
