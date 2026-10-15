# SiagaWarga AI Inference Service

A lightweight, production-ready FastAPI microservice for zero-shot image classification of Indonesian citizen infrastructure reports using CLIP (`openai/clip-vit-base-patch32`).

---

## 1. Overview & Architecture

SiagaWarga enables citizens to report local public infrastructure issues such as potholes, flooding, fallen trees, and uncollected waste. This service provides automated visual category prediction.

### Key Architectural Decisions
- **One-time Model Loading**: The model weights and processor are initialized once during application startup via FastAPI `lifespan`, preventing per-request cold-start latency.
- **Precomputed Text Embeddings**: Because the candidate report categories are fixed, their normalized text prompt embeddings are computed once at startup. Each incoming image only runs through the vision encoder followed by a fast dot product and softmax.
- **Gradient-Free Inference**: Image encoding and score calculation execute strictly inside `torch.no_grad()`.
- **Zero Priority Scoring**: This service only classifies image categories. Urgency or priority calculation is handled downstream by the SiagaWarga application backend.
- **Privacy & Safe Logging**: Image binary bytes and sensitive metadata are never printed to application logs.

### Candidate Categories
| Canonical Category ID | Display Label | Candidate Prompt |
| :--- | :--- | :--- |
| `pothole` | Pothole | `"a pothole in a road"` |
| `cracked_road` | Cracked Road | `"a cracked road"` |
| `flooded_road` | Flooded Road | `"a flooded road"` |
| `fallen_tree` | Fallen Tree | `"a fallen tree"` |
| `garbage` | Garbage | `"garbage on the street"` |
| `broken_street_light` | Broken Street Light | `"a broken street light"` |

---

## 2. Score Semantics

> [!IMPORTANT]
> The score returned in `relative_candidate_score` represents the **relative softmax distribution** over the closed set of candidate categories based on cosine similarity with candidate prompts.
> 
> **What it is NOT:**
> - It is **not** a calibrated real-world probability.
> - It is **not** an open-world confidence or model accuracy metric.
> 
> If an unrelated image (e.g., an indoor cat or a receipt) is submitted, the candidate scores will still sum to `1.0` distributed across the 6 infrastructure labels. The downstream application backend should combine this signal with citizen inputs, geofencing, and validation rules.

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10+ (recommended 3.10 or 3.11)
- ~2GB free disk space (for PyTorch and Hugging Face model cache)

### Step 1: Create Virtual Environment
```bash
# Navigate to the ai-service folder
cd ai-service

# Create virtual environment
python -m venv venv

# Activate on Linux/macOS:
source venv/bin/activate

# Activate on Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> [!NOTE]
> On first startup, Hugging Face Transformers will download `openai/clip-vit-base-patch32` (~600MB) from the Hugging Face Hub to your local cache (`~/.cache/huggingface/hub`). Subsequent launches will use the cached weights offline.

---

## 4. Running the Service

### Start Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Production Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop --http httptools
```
*(Note: Since the model resides in memory, a single worker with thread pool or GPU batching is recommended per container to conserve RAM).*

---

## 5. API Reference & Sample Requests

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### 1. Health Check
Checks service readiness and verifies that the model has loaded into memory.

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_id": "openai/clip-vit-base-patch32",
  "device": "cpu"
}
```

---

### 2. Classify Image
Accepts an image file upload via `multipart/form-data`.

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/classify-image" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/pothole.jpg;type=image/jpeg"
```

**Response (`200 OK`):**
```json
{
  "model_id": "openai/clip-vit-base-patch32",
  "score_semantics": "relative_candidate_score",
  "predicted_category": {
    "category_id": "pothole",
    "display_label": "Pothole",
    "score": 0.8842
  },
  "candidates": [
    {
      "category_id": "pothole",
      "display_label": "Pothole",
      "score": 0.8842
    },
    {
      "category_id": "cracked_road",
      "display_label": "Cracked Road",
      "score": 0.0521
    },
    {
      "category_id": "flooded_road",
      "display_label": "Flooded Road",
      "score": 0.0315
    },
    {
      "category_id": "garbage",
      "display_label": "Garbage",
      "score": 0.0182
    },
    {
      "category_id": "fallen_tree",
      "display_label": "Fallen Tree",
      "score": 0.0095
    },
    {
      "category_id": "broken_street_light",
      "display_label": "Broken Street Light",
      "score": 0.0045
    }
  ]
}
```

---

### 3. Error Responses

| Scenario | HTTP Status | Response Example |
| :--- | :--- | :--- |
| Missing file in form data | `422 Unprocessable Entity` | `{"detail": [{"loc": ["body", "file"], "msg": "Field required"}]}` |
| Unsupported file type (e.g. `.pdf`, `.txt`) | `400 Bad Request` | `{"detail": "Unsupported content type 'text/plain'. Allowed formats: image/jpeg, image/jpg, image/png, image/webp"}` |
| Empty / 0-byte file | `400 Bad Request` | `{"detail": "Empty file uploaded."}` |
| File size > 15MB | `413 Request Entity Too Large` | `{"detail": "File exceeds maximum allowed size of 15MB."}` |
| Corrupted or invalid image bytes | `400 Bad Request` | `{"detail": "Uploaded file is corrupted or not a valid image."}` |
| Model not loaded / uninitialized | `503 Service Unavailable` | `{"detail": "Model is not initialized or still loading."}` |

---

## 6. Automated Testing

Run the automated test suite covering health check, image validation, error handling, and response schema:

```bash
pytest tests/test_api.py -v
```

---

## 7. Offline Evaluation Benchmark

An offline evaluation script is provided in `evaluation/evaluate.py` to benchmark classifier performance on labeled test datasets.

```bash
python evaluation/evaluate.py --csv evaluation/samples.csv
```

Outputs top-1 accuracy, per-class recall, and latency metrics across test samples.

---

## 8. Deployment Notes & Hardware Requirements

- **Model Weight Size**: ~600MB (`openai/clip-vit-base-patch32`).
- **Memory Footprint**:
  - Base PyTorch + Transformers runtime: ~400MB RAM.
  - CLIP model loaded in float32: ~600MB RAM.
  - Recommended minimum container RAM: **1.5GB to 2GB** on CPU.
- **Latency Expectations**:
  - **CPU (Modern x86_64 / ARM64)**: ~80ms – 250ms per image inference.
  - **GPU (CUDA / T4 / A10G)**: ~15ms – 35ms per image inference.
- **Baseline Preservation**: The existing prototype script `../test.py` remains unchanged at the root of the repository for reference.
