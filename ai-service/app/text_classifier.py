import logging
from typing import Dict, List, Any
from transformers import pipeline

logger = logging.getLogger(__name__)

HORIZON_MODEL_NAME = "Horizon-Labs/multilingual-zeroshot-small"

# Label prompts mapping ke taxonomy canonical SiagaWarga
TEXT_LABEL_PROMPTS = {
    "a road surface with a clear hole or pothole": "pothole",
    "cracked, broken, or peeling asphalt without a clear hole": "cracked_road",
    "rainwater or floodwater covering the road surface": "flooded_road",
    "a fallen tree or fallen branch blocking or endangering the road": "fallen_tree",
    "a pile of garbage or scattered waste along the roadside": "garbage",
    "a broken streetlight or a streetlight that does not turn on": "broken_street_light",
    "a public complaint unrelated to infrastructure problems": "other_or_unclear",
}

DISPLAY_LABELS = {
    "pothole": "Jalan Berlubang",
    "cracked_road": "Jalan Retak/Rusak",
    "flooded_road": "Jalan Tergenang",
    "fallen_tree": "Pohon Tumbang",
    "garbage": "Sampah Menumpuk",
    "broken_street_light": "Lampu Jalan Rusak",
    "other_or_unclear": "Lainnya/Belum Jelas",
}


class HorizonTextClassifier:
    """
    Zero-shot text classifier menggunakan Horizon multilingual model
    untuk laporan masyarakat berbahasa Indonesia.
    """

    def __init__(self, model_name: str = HORIZON_MODEL_NAME, device: int = -1):
        self.model_name = model_name
        logger.info("Initializing HorizonTextClassifier with model %s...", self.model_name)
        self.classifier = pipeline(
            "zero-shot-classification",
            model=self.model_name,
            device=device,
        )
        self.candidate_prompts = list(TEXT_LABEL_PROMPTS.keys())
        logger.info("HorizonTextClassifier initialized successfully.")

    def classify_text(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "model_id": self.model_name,
                "score_semantics": "zero_shot_probability",
                "predicted_category": {
                    "category_id": "other_or_unclear",
                    "display_label": DISPLAY_LABELS["other_or_unclear"],
                    "score": 0.0,
                },
                "candidates": [],
            }

        out = self.classifier(text, self.candidate_prompts, multi_label=False)
        labels = out["labels"]
        scores = out["scores"]

        candidates = []
        for prompt, score in zip(labels, scores):
            cat_id = TEXT_LABEL_PROMPTS.get(prompt, "other_or_unclear")
            candidates.append({
                "category_id": cat_id,
                "display_label": DISPLAY_LABELS.get(cat_id, cat_id),
                "score": round(float(score), 4),
            })

        top = candidates[0] if candidates else {
            "category_id": "other_or_unclear",
            "display_label": DISPLAY_LABELS["other_or_unclear"],
            "score": 0.0,
        }

        return {
            "model_id": self.model_name,
            "score_semantics": "zero_shot_probability",
            "predicted_category": top,
            "candidates": candidates,
        }
