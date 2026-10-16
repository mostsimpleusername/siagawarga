# SiagaWarga

Platform Intelligent Citizen Reporting & Response Prioritization berbasis AI — memudahkan warga melaporkan permasalahan lingkungan dan membantu petugas memprioritaskan penanganan berdasarkan Priority Score.

## Struktur Repositori Monorepo

```
SiagaWarga/
├── backend/            # Backend FastAPI (Clean Architecture)
│   ├── alembic/        # Migrasi database
│   ├── app/            # Domain, use cases, presentation, infrastructure
│   ├── tests/          # Test suite
│   ├── main.py         # Entrypoint FastAPI (app = FastAPI(...))
│   ├── pyproject.toml  # Konfigurasi entrypoint Vercel
│   ├── requirements.txt# Dependensi Python backend
│   └── .env.example    # Template environment variables
├── frontend/           # Frontend SPA (React 18 + Vite)
│   ├── src/            # Source code komponen & halaman React
│   ├── public/         # Static assets
│   ├── package.json    # Dependensi frontend
│   └── vite.config.js  # Konfigurasi Vite
├── ai-service/         # Microservice AI (FastAPI + CLIP/Transformers)
│   └── ...             # Dihosting terpisah (Railway/Render/VPS)
├── vercel.json         # Konfigurasi multi-service deployment Vercel
└── README.md
```

## Deploy ke Vercel

Repositori ini dikonfigurasi untuk deployment ke Vercel menggunakan fitur **Vercel Services** (`vercel.json`), dengan 2 service aktif:
- `app`: Service Backend FastAPI yang berada di folder `backend/`
- `frontend`: Service Frontend Vite + React yang berada di folder `frontend/`

> [!NOTE]
> `ai-service` menggunakan model deep learning (PyTorch, CLIP, HuggingFace Transformers ~600MB) sehingga melebihi batas bundle serverless Vercel (500MB). Microservice ini dihosting secara terpisah (misalnya di Railway, Render, Fly.io, atau VPS GPU/CPU) dan dihubungkan ke backend via environment variable `AI_SERVICE_URL`.

### Environment Variables yang Harus Diisi di Dashboard Vercel

Buka **Vercel Dashboard > Project Settings > Environment Variables**, lalu tambahkan variabel berikut untuk target Production / Preview:

| Variabel | Keterangan | Contoh Nilai |
| --- | --- | --- |
| `DATABASE_URL` | Koneksi database PostgreSQL/Supabase (Gunakan transaction pooler port 6543 untuk Supabase) | `postgresql://postgres.xxx:pass@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres` |
| `SECRET_KEY` | Kunci rahasia untuk enkripsi JWT | `openssl rand -hex 32` |
| `ALGORITHM` | Algoritma JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durasi token akses (menit) | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Durasi token refresh (hari) | `7` |
| `BASE_URL` | URL domain publik frontend/backend Vercel | `https://siagawarga.vercel.app` |
| `CORS_ORIGINS` | Origin yang diizinkan (atau `*` untuk publik) | `*` atau `https://siagawarga.vercel.app` |
| `AI_SERVICE_URL` | URL public endpoint microservice AI yang dihosting terpisah | `https://ai.siagawarga.id` |
| `AI_SERVICE_TIMEOUT` | Timeout request ke AI service (detik) | `30` |
| `MAIL_USERNAME` | Akun SMTP untuk pengiriman email verifikasi (opsional) | `noreply@siagawarga.id` |
| `MAIL_PASSWORD` | Password atau App Password SMTP | `xxxx-xxxx-xxxx-xxxx` |
| `MAIL_FROM` | Alamat pengirim email | `noreply@siagawarga.id` |
| `MAIL_PORT` | Port server SMTP | `587` |
| `MAIL_SERVER` | Host server SMTP | `smtp.gmail.com` |
| `MAIL_STARTTLS` | Penggunaan STARTTLS | `True` |
| `MAIL_SSL_TLS` | Penggunaan SSL/TLS | `False` |

## Pengembangan Lokal

### 1. Menjalankan Backend
```bash
cd backend
python -m venv .venv
# Aktifkan virtualenv (Windows: .venv\Scripts\activate, Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Menjalankan Frontend
```bash
cd frontend
npm install
npm run dev
```
Buka browser di `http://localhost:5173`.