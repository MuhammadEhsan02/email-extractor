
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_healthcheck():
    """Test the health check endpoint returns 200 OK."""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("app.services.extraction_service.ExtractionService.create_job")
def test_extract_endpoint(mock_create_job):
    """Test initiating an extraction job (mocking the service layer)."""
    # Mock the service response
    mock_create_job.return_value = "job-uuid-1234"
    
    payload = {
        "input_data": "https://example.com",
        "mode": "quick",
        "config": {"max_urls_per_domain": 1}
    }
    
    response = client.post("/api/v1/extract/", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] == "job-uuid-1234"
    assert data["status"] == "queued"

def test_extract_invalid_payload():
    """Test validation error on empty input."""
    payload = {"input_data": ""} # Too short/empty
    response = client.post("/api/v1/extract/", json=payload)
    assert response.status_code == 422 # HTTP 422 Validation Error

@patch("app.services.file_service.FileService.get_encrypted_file_path")
@patch("os.path.exists")
def test_decrypt_file_not_found(mock_exists, mock_get_path):
    """Test decryption request handles missing files correctly."""
    mock_get_path.return_value = "/fake/path/file.enc"
    mock_exists.return_value = False
    
    payload = {
        "file_id": "non-existent-id",
        "passphrase": "valid-passphrase"
    }
    
    response = client.post("/api/v1/decrypt/", json=payload)
    assert response.status_code == 404