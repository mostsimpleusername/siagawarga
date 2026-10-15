import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Mapping Canonical AI category_id ke Nama Kategori Master DB
AI_TO_DB_CATEGORY_MAP = {
    "pothole": "Jalan Berlubang",
    "cracked_road": "Jalan Retak/Rusak",
    "flooded_road": "Jalan Tergenang",
    "garbage": "Sampah Menumpuk",
    "fallen_tree": "Pohon Tumbang",
    "broken_street_light": "Lampu Jalan Rusak",
    "other_or_unclear": "Lainnya",
}


class AIServiceClient:
    """
    HTTP Client untuk berkomunikasi dengan microservice AI (CLIP + Horizon).
    Menerapkan graceful fallback jika AI service offline/timeout (KNF-05).
    """

    def __init__(self, base_url: str = "http://localhost:8001", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def classify_report(
        self,
        image_bytes: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        content_type: Optional[str] = None,
        deskripsi: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Memanggil endpoint multimodal /api/v1/classify-report di ai-service.
        Mengembalikan rekomendasi AI atau None jika terjadi kegagalan jaringan.
        """
        url = f"{self.base_url}/api/v1/classify-report"
        files = {}
        data = {}

        if deskripsi:
            data["deskripsi"] = deskripsi

        if image_bytes and image_filename:
            files["file"] = (image_filename, image_bytes, content_type or "image/jpeg")

        if not files and not data:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, data=data, files=files if files else None)
                if res.status_code == 200:
                    payload = res.json()
                    ai_cat = payload.get("category")
                    payload["recommended_db_category"] = AI_TO_DB_CATEGORY_MAP.get(ai_cat, "Lainnya")
                    return payload
                logger.warning("AI service returned non-200: %d - %s", res.status_code, res.text)
                return None
        except Exception as exc:
            logger.warning("Failed to connect to AI service at %s: %s", url, exc)
            return None

    def map_to_db_category(self, ai_category_id: str) -> str:
        return AI_TO_DB_CATEGORY_MAP.get(ai_category_id, "Lainnya")
