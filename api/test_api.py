import pytest
from fastapi.testclient import TestClient
from main import app
from sct_generator import generate_sct, Part
import json

client = TestClient(app)

# --- Unit Tests for sct_generator.py ---

def test_sct_generation_structure():
    """Test that SCT byte string generation produces the exact expected Sketch Cut Pro format."""
    parts = [
        Part(length=500, width=300, quantity=2),
        Part(length=1200, width=600, quantity=1)
    ]
    sct_content = generate_sct(parts)
    
    # Assert return type
    assert isinstance(sct_content, str)
    
    # Assert structural integrity 
    lines = sct_content.strip().split('\n')
    assert "<V4.0i>" in lines[0]
    
    # Check that our specific dimensions exist in the byte string format "LengthXWidthXQuantity"
    assert any("500X300X2" in line for line in lines)
    assert any("1200X600X1" in line for line in lines)


# --- Endpoint Integration Tests for main.py ---

def test_read_root():
    """Test that the frontend HTML is served properly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SCT Extractor" in response.text


def test_generate_sct_endpoint():
    """Test the POST endpoint for SCT generation works over HTTP correctly."""
    request_data = {
        "parts": [
            {"length": 450, "width": 450, "quantity": 4}
        ]
    }
    
    response = client.post("/api/generate-sct", json=request_data)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers["content-disposition"]
    assert ".sct" in response.headers["content-disposition"]
    
    content = response.content.decode("utf-8")
    assert "<V4.0i>" in content
    assert "450X450X4" in content


def test_extract_endpoint_without_files():
    """Test that the API rejects requests without the mandatory files field."""
    response = client.post("/api/extract")
    assert response.status_code == 422 # Unprocessable Entity (Missing field)


def test_extract_endpoint_empty_file_list():
    """Test behavior when files array is completely empty."""
    # Sending multipart data with an empty field
    files = {"files": ("", b"")}
    response = client.post("/api/extract", files=files)
    # Different FastAPIs handle empty files differently, typically 400 or 422
    assert response.status_code in [400, 422]
