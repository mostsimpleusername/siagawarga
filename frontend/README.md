# Frontend SiagaWarga

Direktori ini disiapkan untuk antarmuka pengguna (Web / Mobile App) SiagaWarga.

## Panduan Integrasi API Backend

Backend berjalan di `http://127.0.0.1:8000` dengan dokumentasi interaktif:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`
- **Test Bench:** `http://127.0.0.1:8000/test/`

### Endpoint Utama untuk Frontend:
1. **Autentikasi:**
   - `POST /api/v1/auth/register` (Registrasi Warga tanpa NIK)
   - `POST /api/v1/auth/login` (Login email/no HP & kata sandi)
   - `GET /api/v1/auth/me` (Profil pengguna aktif dengan Bearer token)
2. **Laporan Warga:**
   - `POST /api/v1/laporan/assist-ai` (Rekomendasi AI dari foto/deskripsi)
   - `POST /api/v1/laporan` (Kirim laporan baru dengan koordinat GPS)
   - `GET /api/v1/laporan/saya` (Riwayat laporan milik warga)
   - `GET /api/v1/laporan/sekitar` (Laporan sekitar GPS dengan privasi nama pelapor)
   - `GET /api/v1/laporan/{id}/status` (Pelacakan timeline kronologis laporan)
3. **Peta & Spasial:**
   - `GET /api/v1/spasial/peta/geojson` (Data GeoJSON untuk Leaflet / Mapbox)
   - `GET /api/v1/spasial/deteksi-serupa` (Pengecekan potensi duplikasi)
4. **Petugas (Role Petugas):**
   - `GET /api/v1/petugas/laporan` (Daftar semua laporan dengan pagination & filter)
   - `POST /api/v1/petugas/laporan/{id}/verifikasi` (Verifikasi laporan masuk)
   - `PATCH /api/v1/petugas/laporan/{id}/status` (Update status penanganan)
   - `GET /api/v1/prioritas` (Antrean prioritas real-time & clustering P1/P2/P3)
