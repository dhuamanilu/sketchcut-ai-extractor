import pytest
from fastapi.testclient import TestClient

# Import from the new MVC structure
from app.main import app
from app.services.sct_builder import generate_sct
from app.models.schemas import Part

client = TestClient(app)

# --- Unit Tests for sct_builder.py ---

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


def test_generate_sct_banding_and_grooves():
    """Test that banding and grooves are routed to the correct physical dimension."""
    parts = [
        Part(
            length=200, width=500, quantity=1,
            banding_long="1_grueso", banding_short="none",
            groove_long="1", groove_short="none"
        ),
        Part(
            length=800, width=300, quantity=1,
            banding_long="none", banding_short="1_delgado",
            groove_long="none", groove_short="2"
        ),
        Part(
            length=600, width=600, quantity=1,
            banding_long="mixto", banding_short="mixto",
            groove_long="1", groove_short="none"
        )
    ]
    sct_content = generate_sct(parts)
    lines = sct_content.strip().split('\n')
    
    # physical Largo for part 1 is 500 (Width axis), Corto is 200 (Length axis)
    # banding_long is "1_grueso" (val 1) and groove_long is "1" (val 1)
    # Target string is Length_c X Width_c _ Length_g X Width_g -> 0X1_0X1
    assert any("0X1_0X1" in line for line in lines)
    
    # physical Largo for part 2 is 800 (Length axis), Corto is 300 (Width axis)
    # banding_short is "1_delgado" (val 3) and groove_short is "2" (val 2)
    # Target string is Length_c X Width_c _ Length_g X Width_g -> 0X3_0X2
    assert any("0X3_0X2" in line for line in lines)
    
    # part 3 is a perfect square, "mixto" (val 5) for both
    # groove_long is "1" (val 1)
    # Target string -> 5X5_1X0
    assert any("5X5_1X0" in line for line in lines)


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
