import io
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.classifier import CLIPClassifier, MODEL_NAME
from app.text_classifier import HorizonTextClassifier, HORIZON_MODEL_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("siagawarga.ai_service")

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024


class CandidateScore(BaseModel):
    category_id: str
    display_label: str
    score: float


class ClassificationResponse(BaseModel):
    model_id: str
    score_semantics: str
    predicted_category: CandidateScore
    candidates: List[CandidateScore]


class FusionReportResponse(BaseModel):
    category: str
    display_label: str
    confidence_score: float
    review_required: bool
    review_reason: Optional[str] = None
    vision_prediction: Optional[CandidateScore] = None
    text_prediction: Optional[CandidateScore] = None
    model_metadata: dict


class HealthResponse(BaseModel):
    status: str
    clip_loaded: bool
    horizon_loaded: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SiagaWarga AI Multimodal Service (CLIP + Horizon)...")
    start_time = time.time()
    try:
        app.state.classifier = CLIPClassifier()
    except Exception as e:
        logger.error("Failed to load CLIP classifier: %s", str(e), exc_info=True)
        app.state.classifier = None

    try:
        app.state.text_classifier = HorizonTextClassifier()
    except Exception as e:
        logger.error("Failed to load Horizon text classifier: %s", str(e), exc_info=True)
        app.state.text_classifier = None

    logger.info("Lifespan init finished in %.2fs", time.time() - start_time)
    yield
    logger.info("Shutting down AI service.")


app = FastAPI(
    title="SiagaWarga Multimodal AI Inference API",
    description="Zero-shot vision (CLIP) & text (Horizon) inference service for SiagaWarga.",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    clip_ok = getattr(app.state, "classifier", None) is not None
    horizon_ok = getattr(app.state, "text_classifier", None) is not None
    status_str = "healthy" if (clip_ok and horizon_ok) else "degraded"
    return {
        "status": status_str,
        "clip_loaded": clip_ok,
        "horizon_loaded": horizon_ok,
    }


@app.post("/api/v1/classify-image", response_model=ClassificationResponse, tags=["Inference"])
async def classify_image(file: UploadFile = File(...)):
    classifier: CLIPClassifier = getattr(app.state, "classifier", None)
    if classifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLIP model is not initialized.",
        )

    if not file.content_type or file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type '{file.content_type}'.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum size.")

    try:
        with Image.open(io.BytesIO(contents)) as pil_img:
            pil_img.verify()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    return classifier.classify(image)


@app.post("/api/v1/classify-text", response_model=ClassificationResponse, tags=["Inference"])
async def classify_text(text: str = Form(...)):
    text_clf: HorizonTextClassifier = getattr(app.state, "text_classifier", None)
    if text_clf is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Horizon text model is not initialized.",
        )
    return text_clf.classify_text(text)


@app.post("/api/v1/classify-report", response_model=FusionReportResponse, tags=["Inference"])
async def classify_report(
    file: Optional[UploadFile] = File(None),
    deskripsi: Optional[str] = Form(None),
):
    """
    Multimodal fusion classifier (PRD KNF-10 & Section 6-7 AI Plan):
    Menggabungkan analisis visual foto (CLIP) dan deskripsi teks (Horizon).
    """
    classifier: CLIPClassifier = getattr(app.state, "classifier", None)
    text_clf: HorizonTextClassifier = getattr(app.state, "text_classifier", None)

    vision_pred = None
    if file and file.filename:
        try:
            contents = await file.read()
            if contents and len(contents) <= MAX_FILE_SIZE_BYTES:
                image = Image.open(io.BytesIO(contents)).convert("RGB")
                if classifier:
                    v_res = classifier.classify(image)
                    vision_pred = v_res["predicted_category"]
        except Exception as e:
            logger.warning("Vision classification in fusion skipped: %s", e)

    text_pred = None
    if deskripsi and deskripsi.strip() and text_clf:
        try:
            t_res = text_clf.classify_text(deskripsi)
            text_pred = t_res["predicted_category"]
        except Exception as e:
            logger.warning("Text classification in fusion skipped: %s", e)

    # Fusion logic
    if vision_pred and text_pred:
        cat_v = vision_pred["category_id"]
        cat_t = text_pred["category_id"]

        if cat_v == cat_t:
            # Saling sepakat
            final_cat = cat_v
            final_label = vision_pred["display_label"]
            score = max(vision_pred["score"], text_pred["score"])
            review_required = False
            review_reason = None
        else:
            # Ketidakcocokan (disagreement) -> KNF-10 flagging
            final_cat = cat_v  # default prefer visual evidence
            final_label = vision_pred["display_label"]
            score = vision_pred["score"]
            review_required = True
            review_reason = f"Foto mendeteksi '{cat_v}', sedangkan deskripsi teks mengindikasikan '{cat_t}'."
    elif vision_pred:
        final_cat = vision_pred["category_id"]
        final_label = vision_pred["display_label"]
        score = vision_pred["score"]
        review_required = score < 0.40
        review_reason = "Tingkat keyakinan model visual di bawah ambang batas" if review_required else None
    elif text_pred:
        final_cat = text_pred["category_id"]
        final_label = text_pred["display_label"]
        score = text_pred["score"]
        review_required = score < 0.40
        review_reason = "Tingkat keyakinan model teks di bawah ambang batas" if review_required else None
    else:
        final_cat = "other_or_unclear"
        final_label = "Lainnya/Belum Jelas"
        score = 0.0
        review_required = True
        review_reason = "Tidak ada bukti foto maupun teks yang memadai"

    return FusionReportResponse(
        category=final_cat,
        display_label=final_label,
        confidence_score=score,
        review_required=review_required,
        review_reason=review_reason,
        vision_prediction=CandidateScore(**vision_pred) if vision_pred else None,
        text_prediction=CandidateScore(**text_pred) if text_pred else None,
        model_metadata={
            "clip_model": MODEL_NAME,
            "horizon_model": HORIZON_MODEL_NAME,
        },
    )
