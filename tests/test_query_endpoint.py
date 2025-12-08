import pytest
from fastapi.testclient import TestClient
from main import app
from api.chatbot import QueryRequest
from unittest.mock import patch, MagicMock
from services.retrieval import retrieval_service
from services.content_loader import content_loader
from services.vector_store import vector_store


# Create a test client for the FastAPI app
client = TestClient(app)


def test_query_endpoint_success():
    """
    Test the /query endpoint with a successful response
    """
    # Mock the retrieval service to return known content
    with patch.object(retrieval_service, 'retrieve_relevant_content') as mock_retrieve:
        mock_retrieve.return_value = [
            {
                'id': 'test_id_1',
                'content': 'This is test content about robotics.',
                'metadata': {'source': 'test.md', 'chunk_id': 0},
                'similarity': 0.9
            }
        ]

        # Send a test request to the query endpoint
        response = client.post(
            "/query",
            json={"text": "What is robotics?"},
            headers={"X-API-Key": "test_key"}
        )

        # Assert the response status code
        assert response.status_code == 200

        # Assert the response structure
        data = response.json()
        assert "text" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["id"] == "test_id_1"
        assert "robotics" in data["text"].lower()


def test_query_endpoint_no_content():
    """
    Test the /query endpoint when no relevant content is found
    """
    # Mock the retrieval service to return no content
    with patch.object(retrieval_service, 'retrieve_relevant_content') as mock_retrieve:
        mock_retrieve.return_value = []

        # Send a test request to the query endpoint
        response = client.post(
            "/query",
            json={"text": "What is artificial intelligence?"},
            headers={"X-API-Key": "test_key"}
        )

        # Assert the response status code
        assert response.status_code == 200

        # Assert the response structure
        data = response.json()
        assert "text" in data
        assert "sources" in data
        assert len(data["sources"]) == 0


def test_query_endpoint_with_selected_text():
    """
    Test the /query endpoint with selected text parameter
    """
    # Mock the retrieval service to return known content
    with patch.object(retrieval_service, 'retrieve_relevant_content') as mock_retrieve:
        mock_retrieve.return_value = [
            {
                'id': 'selected_id',
                'content': 'This specific text was selected.',
                'metadata': {'source': 'selection', 'chunk_id': 0, 'type': 'selection'},
                'similarity': 1.0
            }
        ]

        # Send a test request with selected text
        response = client.post(
            "/query",
            json={
                "text": "Explain this",
                "selected_text": "This specific text was selected."
            },
            headers={"X-API-Key": "test_key"}
        )

        # Assert the response status code
        assert response.status_code == 200

        # Assert the response structure
        data = response.json()
        assert "text" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["id"] == "selected_id"


def test_query_endpoint_missing_text():
    """
    Test the /query endpoint with missing text parameter
    """
    # Send a request without the required text parameter
    response = client.post(
        "/query",
        json={},
        headers={"X-API-Key": "test_key"}
    )

    # Should return 422 (validation error) because text is required
    assert response.status_code == 422


def test_query_endpoint_invalid_api_key():
    """
    Test the /query endpoint with invalid API key
    """
    # Send a request with invalid API key
    response = client.post(
        "/query",
        json={"text": "What is robotics?"},
        headers={"X-API-Key": "invalid_key"}
    )

    # Should return 401 (unauthorized) because of invalid API key
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main()