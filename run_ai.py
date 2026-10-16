"""
Script untuk menjalankan Microservice AI Multimodal SiagaWarga (port 8001).
Dapat dijalankan langsung dari root proyek:
    python run_ai.py
atau
    uvicorn app.main:app --app-dir ai-service --port 8001 --reload
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  SiagaWarga Multimodal AI Service (CLIP + Horizon)")
    print("  Server URL : http://127.0.0.1:8001")
    print("  Health URL : http://127.0.0.1:8001/health")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8001,
        app_dir="ai-service",
        reload=True,
    )
