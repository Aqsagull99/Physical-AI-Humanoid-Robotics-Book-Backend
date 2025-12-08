import pytest
import os
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from services.retrieval import retrieval_service
from services.content_loader import content_loader


# Create a test client for the FastAPI app
client = TestClient(app)


def test_end_to_end_query_flow():
    """
    End-to-end test to verify the query flow and grounding in book content
    """
    # Mock the retrieval service to return known content
    with patch.object(retrieval_service, 'retrieve_relevant_content') as mock_retrieve:
        # Mock content that is clearly grounded in robotics/book content
        mock_retrieve.return_value = [
            {
                'id': 'test_id_1',
                'content': 'Physical AI combines principles of robotics, machine learning, and biomechanics to create systems that interact with the physical world.',
                'metadata': {'file_path': 'physical_ai.md', 'chunk_id': 0, 'type': 'paragraph'},
                'similarity': 0.95
            },
            {
                'id': 'test_id_2',
                'content': 'Humanoid robots are designed to resemble and mimic human behavior and appearance, often featuring articulated limbs and sensory capabilities.',
                'metadata': {'file_path': 'humanoid_robots.md', 'chunk_id': 1, 'type': 'paragraph'},
                'similarity': 0.87
            }
        ]

        # Test the query endpoint
        response = client.post(
            "/query",
            json={"text": "What is Physical AI?"},
            headers={"X-API-Key": "test_key"}
        )

        # Assert the response status code
        assert response.status_code == 200

        # Assert the response structure
        data = response.json()
        assert "text" in data
        assert "sources" in data
        assert len(data["sources"]) == 2  # Should have 2 sources as per our mock

        # Check that the response contains information related to the content
        response_text = data["text"].lower()
        assert "physical ai" in response_text or "robotics" in response_text or "biomechanics" in response_text

        # Check that sources are properly formatted according to spec
        for source in data["sources"]:
            assert "id" in source
            assert "content" in source
            assert "metadata" in source


def test_end_to_end_ingestion_flow():
    """
    End-to-end test to verify the ingestion flow
    """
    # Mock the content loader to return test content
    with patch.object(content_loader, 'load_content') as mock_load_content:
        test_content = [
            {
                'id': 'test_id_1',
                'content': 'This is test content about robotics.',
                'source_file': 'test.md',
                'chunk_index': 0,
                'metadata': {'file_path': 'test.md', 'chunk_id': 0, 'type': 'paragraph', 'content': 'This is test content about robotics.'}
            }
        ]
        mock_load_content.return_value = test_content

        # Test the ingest endpoint
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


def test_health_check_endpoint():
    """
    Test the health check endpoint
    """
    response = client.get("/health")

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response structure
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert data["status"] == "healthy"


def test_content_grounding_percentage():
    """
    Test to verify that responses are grounded in book content
    This is a simplified test - in a real implementation, you'd have more sophisticated grounding checks
    """
    # Mock content that is clearly related to the query
    with patch.object(retrieval_service, 'retrieve_relevant_content') as mock_retrieve:
        mock_retrieve.return_value = [
            {
                'id': 'test_id_1',
                'content': 'Physical AI is an interdisciplinary field combining robotics, machine learning, and biomechanics.',
                'metadata': {'file_path': 'intro.md', 'chunk_id': 0, 'type': 'paragraph'},
                'similarity': 0.92
            }
        ]

        response = client.post(
            "/query",
            json={"text": "What is Physical AI?"},
            headers={"X-API-Key": "test_key"}
        )

        assert response.status_code == 200
        data = response.json()

        # In a real test, we would implement more sophisticated grounding verification
        # For now, we verify that the response includes sources from the retrieved content
        assert len(data["sources"]) > 0
        assert "physical ai" in data["text"].lower()


if __name__ == "__main__":
    pytest.main()