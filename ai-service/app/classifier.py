import logging
from dataclasses import dataclass
from typing import Dict, List, Any
from PIL import Image
import torch
from transformers import CLIPModel, CLIPProcessor

logger = logging.getLogger(__name__)

MODEL_NAME = "openai/clip-vit-base-patch32"


@dataclass(frozen=True)
class CategoryDefinition:
    category_id: str
    display_label: str
    prompt: str


CANDIDATE_CATEGORIES: List[CategoryDefinition] = [
    CategoryDefinition(
        category_id="pothole",
        display_label="Pothole",
        prompt="a pothole in a road",
    ),
    CategoryDefinition(
        category_id="cracked_road",
        display_label="Cracked Road",
        prompt="a cracked road",
    ),
    CategoryDefinition(
        category_id="flooded_road",
        display_label="Flooded Road",
        prompt="a flooded road",
    ),
    CategoryDefinition(
        category_id="fallen_tree",
        display_label="Fallen Tree",
        prompt="a fallen tree",
    ),
    CategoryDefinition(
        category_id="garbage",
        display_label="Garbage",
        prompt="garbage on the street",
    ),
    CategoryDefinition(
        category_id="broken_street_light",
        display_label="Broken Street Light",
        prompt="a broken street light",
    ),
]


class CLIPClassifier:
    """
    CLIP image classifier for SiagaWarga citizen reports.
    Loads CLIP model and processor once, pre-tokenizes candidate text prompts,
    and runs zero-shot inference without gradient calculations.
    """

    def __init__(self, model_name: str = MODEL_NAME, device: str = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.categories = CANDIDATE_CATEGORIES
        self.prompts = [c.prompt for c in self.categories]

        logger.info("Initializing CLIPClassifier with model %s on %s...", self.model_name, self.device)
        self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model.eval()

        # Pre-tokenize candidate prompts once during startup
        raw_text_inputs = self.processor(
            text=self.prompts,
            return_tensors="pt",
            padding=True,
        )
        self.text_inputs = {k: v.to(self.device) for k, v in raw_text_inputs.items()}
        logger.info("CLIPClassifier initialized successfully with %d categories.", len(self.categories))

    def classify(self, image: Image.Image) -> Dict[str, Any]:
        """
        Classifies an input PIL image against the candidate categories.
        Returns candidate relative scores and top predicted category.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")

        raw_image_inputs = self.processor(images=image, return_tensors="pt")
        image_inputs = {k: v.to(self.device) for k, v in raw_image_inputs.items()}

        # Combine pre-tokenized text and image inputs
        inputs = {**self.text_inputs, **image_inputs}

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = outputs.logits_per_image.softmax(dim=1)[0].cpu().tolist()

        scored_candidates = [
            {
                "category_id": cat.category_id,
                "display_label": cat.display_label,
                "score": round(prob, 4),
            }
            for cat, prob in zip(self.categories, probabilities)
        ]

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidate = scored_candidates[0]

        return {
            "model_id": self.model_name,
            "score_semantics": "relative_candidate_score",
            "predicted_category": top_candidate,
            "candidates": scored_candidates,
        }
