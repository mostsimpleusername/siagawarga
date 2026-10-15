"""
Test Suite End-to-End untuk SiagaWarga (PRD Compliance).
Menguji:
- Root & Health Check DB (Supabase)
- Perhitungan Priority Score (DomainPriorityEngine)
- Autentikasi Warga (Registrasi & Login)
- Analitik Spasial & Peta
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from main import app
from app.domain.enums import KategoriPrioritas, Severity
from app.use_cases.prioritas.priority_engine import DomainPriorityEngine

client = TestClient(app)


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
