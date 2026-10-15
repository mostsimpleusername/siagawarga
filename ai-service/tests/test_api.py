import io
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.classifier import MODEL_NAME


@pytest.fixture
def mock_classifier():
    """Provides a mock CLIPClassifier to allow fast and deterministic unit testing."""
    mock = MagicMock()
    mock.model_name = MODEL_NAME
    mock.device = "cpu"
    mock.classify.return_value = {
        "model_id": MODEL_NAME,
        "score_semantics": "relative_candidate_score",
        "predicted_category": {
            "category_id": "pothole",
            "display_label": "Pothole",
            "score": 0.8842,
        },
        "candidates": [
            {"category_id": "pothole", "display_label": "Pothole", "score": 0.8842},
            {"category_id": "cracked_road", "display_label": "Cracked Road", "score": 0.0521},
            {"category_id": "flooded_road", "display_label": "Flooded Road", "score": 0.0315},
            {"category_id": "garbage", "display_label": "Garbage", "score": 0.0182},
            {"category_id": "fallen_tree", "display_label": "Fallen Tree", "score": 0.0095},
            {"category_id": "broken_street_light", "display_label": "Broken Street Light", "score": 0.0045},
        ],
    }
    return mock


@pytest.fixture
def client(mock_classifier):
    """Initializes TestClient with injected classifier state."""
    app.state.classifier = mock_classifier
    with TestClient(app) as test_client:
        yield test_client


def _create_test_image_bytes(format: str = "JPEG") -> bytes:
    """Helper to generate a valid in-memory image byte buffer."""
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(73, 109, 137))
    img.save(buf, format=format)
    return buf.getvalue()


def test_health_endpoint_healthy(client):
    """Asserts GET /health returns 200 OK and expected status fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["model_id"] == MODEL_NAME
    assert "device" in data


def test_health_endpoint_uninitialized(client):
    """Asserts GET /health returns 503 if model is not loaded."""
    app.state.classifier = None
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["model_loaded"] is False


def test_classify_missing_file_payload(client):
    """Asserts 422 Unprocessable Entity when no file part is provided."""
    response = client.post("/api/v1/classify-image")
    assert response.status_code == 422


def test_classify_invalid_content_type(client):
    """Asserts 400 Bad Request when an unsupported content-type (e.g., text/plain) is uploaded."""
    files = {
        "file": ("report.txt", b"This is a text log not an image", "text/plain")
    }
    response = client.post("/api/v1/classify-image", files=files)
    assert response.status_code == 400
    assert "Unsupported content type" in response.json()["detail"]


def test_classify_empty_file(client):
    """Asserts 400 Bad Request when an empty image file is uploaded."""
    files = {
        "file": ("empty.jpg", b"", "image/jpeg")
    }
    response = client.post("/api/v1/classify-image", files=files)
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_classify_corrupted_image(client):
    """Asserts 400 Bad Request when image bytes are corrupted."""
    corrupted_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00corrupted-junk-data"
    files = {
        "file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")
    }
    response = client.post("/api/v1/classify-image", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_classify_valid_image(client, mock_classifier):
    """Asserts 200 OK and verifies response schema when a valid JPEG is uploaded."""
    img_bytes = _create_test_image_bytes(format="JPEG")
    files = {
        "file": ("street_photo.jpg", img_bytes, "image/jpeg")
    }
    response = client.post("/api/v1/classify-image", files=files)
    assert response.status_code == 200
    data = response.json()

    # Verify response schema fields
    assert data["model_id"] == MODEL_NAME
    assert data["score_semantics"] == "relative_candidate_score"
    assert "predicted_category" in data
    assert "candidates" in data

    predicted = data["predicted_category"]
    assert predicted["category_id"] == "pothole"
    assert predicted["display_label"] == "Pothole"
    assert isinstance(predicted["score"], float)

    # Verify candidates list
    assert len(data["candidates"]) == 6
    assert data["candidates"][0]["category_id"] == "pothole"
    mock_classifier.classify.assert_called_once()
