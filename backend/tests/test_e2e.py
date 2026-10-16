"""
Test Suite End-to-End Komprehensif untuk SiagaWarga (PRD Compliance).
Menguji:
- Root & Health Check DB (Supabase)
- Perhitungan Priority Score (DomainPriorityEngine)
- Autentikasi Warga (Registrasi & Login)
- Siklus Hidup Laporan Warga: Buat, Lihat Riwayat, Pantau Timeline (KF-03 s/d KF-08)
- Privasi Publik & Spasial: Laporan Sekitar dengan Masking Data (KF-07, KNF-04)
- Deteksi Duplikasi Spasial (KF-17)
- Manajemen Petugas: Verifikasi Laporan, Update Status & Catat Penanganan, Audit Trail (KF-09, KF-10, KF-15, KF-16, KF-18)
- Antrean Prioritas Dinamis (KF-13, Sequence Diagram 2)
- Visualisasi Peta GeoJSON (KF-14)
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from app.domain.entities.kategori_laporan import KategoriLaporan
from app.domain.entities.pengguna import Petugas
from app.domain.enums import KategoriPrioritas, Peran, Severity, StatusLaporan
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.security.hashing import hash_kata_sandi
from app.infrastructure.security.jwt_handler import buat_access_token
from app.use_cases.prioritas.priority_engine import DomainPriorityEngine

client = TestClient(app)


def get_or_create_petugas_token() -> str:
    db = SessionLocal()
    try:
        petugas = db.scalar(select(Petugas).where(Petugas.email == "petugas.test@siagawarga.id"))
        if not petugas:
            petugas = Petugas(
                nama="Petugas Command Center Test",
                email="petugas.test@siagawarga.id",
                nomor_hp="081999888777",
                kata_sandi_hash=hash_kata_sandi("petugas12345"),
                peran=Peran.PETUGAS,
                is_aktif=True,
                is_verified=True,
            )
            db.add(petugas)
            db.commit()
            db.refresh(petugas)

        token = buat_access_token(subyek=petugas.id, peran=petugas.peran.value)
        return token
    finally:
        db.close()


def get_first_kategori_id() -> str:
    db = SessionLocal()
    try:
        kategori = db.scalar(select(KategoriLaporan).where(KategoriLaporan.is_aktif.is_(True)))
        if not kategori:
            kategori = KategoriLaporan(
                nama="Jalan Rusak",
                deskripsi="Kerusakan jalan umum, aspal berlubang",
                bobot_bahaya_default=3.0,
                is_aktif=True,
            )
            db.add(kategori)
            db.commit()
            db.refresh(kategori)
        return str(kategori.id)
    finally:
        db.close()


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "SiagaWarga"


def test_health_check_supabase():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_domain_priority_engine_calculation():
    # Skenario 1: Bahaya Tinggi, Lokasi Strategis, Pelapor Banyak, Menunggu 10 jam -> P1 Kritis
    hasil_p1 = DomainPriorityEngine.hitung(
        severity=Severity.TINGGI,
        bobot_kategori=4.0,
        faktor_lokasi=80.0,
        dampak=80.0,
        jumlah_pelapor=5,
        waktu_tunggu_jam=10.0,
    )
    assert hasil_p1.kategori_prioritas == KategoriPrioritas.P1
    assert hasil_p1.skor_prioritas >= 70.0

    # Skenario 2: Bahaya Rendah, Pelapor 1, Baru dibuat -> P3 Rendah
    hasil_p3 = DomainPriorityEngine.hitung(
        severity=Severity.RENDAH,
        bobot_kategori=1.0,
        faktor_lokasi=20.0,
        dampak=20.0,
        jumlah_pelapor=1,
        waktu_tunggu_jam=0.0,
    )
    assert hasil_p3.kategori_prioritas == KategoriPrioritas.P3
    assert hasil_p3.skor_prioritas < 40.0


def test_auth_registration_and_login_flow():
    unique_id = str(uuid.uuid4())[:8]
    email_test = f"warga_test_{unique_id}@example.com"
    pwd_test = "password12345"

    # 1. Registrasi (KF-01)
    reg_payload = {
        "nama": f"Warga Test {unique_id}",
        "email": email_test,
        "nomor_hp": f"0812{unique_id}",
        "kata_sandi": pwd_test,
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["pengguna"]["email"] == email_test

    # 2. Verifikasi email token jika ada link simulasi
    token_url = reg_data.get("tautan_verifikasi_simulasi")
    if token_url and "token=" in token_url:
        token_str = token_url.split("token=")[-1]
        verify_res = client.get(f"/api/v1/auth/verify-email?token={token_str}")
        assert verify_res.status_code == 200

    # 3. Login (KF-02)
    login_payload = {
        "identitas": email_test,
        "kata_sandi": pwd_test,
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 4. Profil /me
    auth_header = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=auth_header)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email_test


def test_laporan_lifecycle_warga_dan_petugas():
    unique_id = str(uuid.uuid4())[:8]
    email_warga = f"pelapor_{unique_id}@example.com"
    pwd = "password12345"

    # 1. Register & verify Warga
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "nama": f"Pelapor Uji {unique_id}",
            "email": email_warga,
            "nomor_hp": f"0813{unique_id}",
            "kata_sandi": pwd,
        },
    )
    assert reg_res.status_code == 201
    token_sim = reg_res.json().get("tautan_verifikasi_simulasi")
    if token_sim:
        client.get(f"/api/v1/auth/verify-email?token={token_sim.split('token=')[-1]}")

    login_res = client.post("/api/v1/auth/login", json={"identitas": email_warga, "kata_sandi": pwd})
    warga_token = login_res.json()["access_token"]
    warga_headers = {"Authorization": f"Bearer {warga_token}"}

    petugas_token = get_or_create_petugas_token()
    petugas_headers = {"Authorization": f"Bearer {petugas_token}"}

    kategori_id = get_first_kategori_id()

    # 2. Buat Laporan Baru Warga (KF-03 s/d KF-06)
    laporan_payload = {
        "kategori_id": kategori_id,
        "judul": f"Jalan Berlubang di Dekat Pasar {unique_id}",
        "deskripsi": "Ada lubang besar sedalam 15cm membahayakan pengendara motor saat malam hari.",
        "alamat_lokasi": "Jl. Merdeka No. 10, RT 02/RW 04",
        "latitude": -6.2088,
        "longitude": 106.8456,
        "severity": "TINGGI",
        "tingkat_bahaya": 75.0,
        "faktor_lokasi": 60.0,
        "dampak": 70.0,
        "foto_urls": ["https://images.unsplash.com/photo-1515162816999-a0c47dc192f7"],
    }
    buat_res = client.post("/api/v1/laporan", json=laporan_payload, headers=warga_headers)
    assert buat_res.status_code == 201
    laporan_data = buat_res.json()
    laporan_id = laporan_data["id"]
    assert laporan_data["status"] == "DIKIRIM"
    assert laporan_data["skor_prioritas"] > 0

    # 3. Warga melihat riwayat laporan saya (KF-07)
    saya_res = client.get("/api/v1/laporan/saya", headers=warga_headers)
    assert saya_res.status_code == 200
    ids_saya = [l["id"] for l in saya_res.json()]
    assert laporan_id in ids_saya

    # 4. Publik melihat laporan sekitar dengan masking privasi KNF-04 (KF-07)
    sekitar_res = client.get("/api/v1/laporan/sekitar?latitude=-6.2088&longitude=106.8456&radius_meter=2000")
    assert sekitar_res.status_code == 200
    sekitar_list = sekitar_res.json()
    assert len(sekitar_list) > 0
    item_target = next((x for x in sekitar_list if x["id"] == laporan_id), None)
    assert item_target is not None
    assert item_target["pelapor"]["nama_anonim"] != ""
    assert "email" not in item_target["pelapor"]  # Privasi terjaga

    # 5. Warga memantau kronologi status (KF-08)
    status_res = client.get(f"/api/v1/laporan/{laporan_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status_terkini"] == "DIKIRIM"
    assert len(status_data["timeline"]) >= 1

    # 6. Petugas melihat daftar semua laporan (KF-09)
    list_res = client.get("/api/v1/petugas/laporan", headers=petugas_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 7. Petugas memverifikasi laporan (KF-10)
    verif_payload = {
        "terima": True,
        "sesuaikan_severity": "TINGGI",
        "catatan": "Laporan valid, tim dinas PU akan diterjunkan.",
    }
    verif_res = client.post(
        f"/api/v1/petugas/laporan/{laporan_id}/verifikasi",
        json=verif_payload,
        headers=petugas_headers,
    )
    assert verif_res.status_code == 200
    assert verif_res.json()["status"] == "DIPROSES"

    # 8. Petugas menyelesaikan laporan & catat penanganan (KF-15, KF-16, KF-18)
    update_payload = {
        "status_baru": "SELESAI",
        "catatan": "Perbaikan jalan telah selesai ditambal oleh tim regu 1.",
    }
    update_res = client.patch(
        f"/api/v1/petugas/laporan/{laporan_id}/status",
        json=update_payload,
        headers=petugas_headers,
    )
    assert update_res.status_code == 200
    detail_selesai = update_res.json()
    assert detail_selesai["status"] == "SELESAI"
    assert any("Perbaikan jalan telah selesai" in r["catatan"] for r in detail_selesai["riwayat_status"])


def test_spasial_urutan_prioritas():
    res = client.get("/api/v1/spasial/prioritas")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_spasial_peta_geojson():
    res = client.get("/api/v1/spasial/peta/geojson")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_spasial_deteksi_serupa():
    kategori_id = get_first_kategori_id()
    res = client.get(
        f"/api/v1/spasial/deteksi-serupa?kategori_id={kategori_id}&latitude=-6.2088&longitude=106.8456&radius_meter=5000"
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_ditemukan" in data
    assert "indikasi_duplikasi" in data
    assert isinstance(data["laporan_serupa"], list)


def test_petugas_antrean_prioritas():
    petugas_token = get_or_create_petugas_token()
    headers = {"Authorization": f"Bearer {petugas_token}"}
    res = client.get("/api/v1/prioritas", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "cluster_per_level" in data
    assert "P1" in data["cluster_per_level"]
    assert "antrean" in data
