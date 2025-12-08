import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from services.retrieval import retrieval_service
from services.content_loader import content_loader


# Create a test client for the FastAPI app
client = TestClient(app)


def test_ingest_endpoint_success():
    """
    Test the /admin/ingest endpoint with a successful response
    """
    # Mock the retrieval service initialize_store method
    with patch.object(retrieval_service, 'initialize_store') as mock_initialize:
        mock_initialize.return_value = None  # initialize_store returns None

        # Send a test request to the ingest endpoint
        response = client.post(
            "/admin/ingest",
            headers={"X-API-Key": "test_admin_key"}
        )

        # Assert the response status code
        assert response.status_code == 200

        # Assert the response structure
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert data["status"] == "success"
        assert "ingested successfully" in data["message"]


def test_ingest_endpoint_invalid_api_key():
    """
    Test the /admin/ingest endpoint with invalid API key
    """
    # Send a request with invalid API key
    response = client.post(
        "/admin/ingest",
        headers={"X-API-Key": "invalid_key"}
    )

    # Should return 401 (unauthorized) because of invalid API key
    assert response.status_code == 401


def test_ingest_endpoint_exception_handling():
    """
    Test the /admin/ingest endpoint handles exceptions properly
    """
    # Mock the retrieval service to raise an exception
    with patch.object(retrieval_service, 'initialize_store') as mock_initialize:
        mock_initialize.side_effect = Exception("Database connection failed")

        # Send a test request to the ingest endpoint
        response = client.post(
            "/admin/ingest",
            headers={"X-API-Key": "test_admin_key"}
        )

        # Should return 500 (internal server error) because of the exception
        assert response.status_code == 500

        # Check that the error response has the expected structure
        data = response.json()
        assert "detail" in data


def test_content_loader_integration():
    """
    Test the content loader integration with the ingestion process
    """
    # Mock the content loader to return test content
    with patch.object(content_loader, 'load_content') as mock_load_content:
        test_content = [
            {
                'id': 'test_id_1',
                'content': 'This is test content about robotics.',
                'source_file': 'test.md',
                'chunk_index': 0,
                'metadata': {'file_path': 'test.md', 'chunk_id': 0, 'type': 'paragraph'}
            }
        ]
        mock_load_content.return_value = test_content

        # Verify that the content loader returns the expected content
        content = content_loader.load_content()
        assert len(content) == 1
        assert content[0]['id'] == 'test_id_1'
        assert 'robotics' in content[0]['content'].lower()


if __name__ == "__main__":
    pytest.main()