import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { API_BASE } from '../config'
import 'leaflet/dist/leaflet.css'

const KATEGORI = [
  { id: '70654e2a-9910-493a-90f9-dc1b4a9db87a', label: 'Saluran Air Tersumbat / Drainase' },
  { id: '66267b29-2275-4459-ac0d-00bb5281925c', label: 'Jalan Berlubang' },
  { id: 'c71eff3d-bc34-4309-a311-2540d27afbef', label: 'Jalan Retak / Rusak' },
  { id: 'ba6b529f-7d20-48f4-8849-8bbfa190bcfb', label: 'Jalan Tergenang / Banjir' },
  { id: '85b522b3-a6fa-4254-bddc-e97e7ab1b266', label: 'Kebersihan & Sampah Menumpuk' },
  { id: '0efa1578-78b2-467c-b3d3-66fbc40419cf', label: 'Lampu Jalan Rusak / Penerangan' },
  { id: 'cd2caef5-04ed-4b41-92f6-8de758c03501', label: 'Pohon Tumbang / Gangguan Pohon' },
  { id: 'bf2ee638-0226-48af-b625-1cc6da8cd16d', label: 'Lainnya / Fasilitas Umum' },
]

// ─── Step 1: Form Isi Laporan ─────────────────────────────────────────────────
function Step1Form({ form, setForm, onNext, userName, userInitials }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markerRef = useRef(null)
  const cameraInputRef = useRef(null)
  const [showMapModal, setShowMapModal] = useState(false)

  // Init Leaflet map saat modal dibuka
  useEffect(() => {
    if (!showMapModal) return
    setTimeout(async () => {
      const L = (await import('leaflet')).default
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })
      if (!mapInstanceRef.current && mapRef.current) {
        const map = L.map(mapRef.current).setView([form.lat, form.lng], 15)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
        }).addTo(map)
        const marker = L.marker([form.lat, form.lng], { draggable: true }).addTo(map)
        
        async function updateCoordsAndAddress(lat, lng) {
          setForm(f => ({ ...f, lat, lng }))
          try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`, {
              headers: { 'Accept-Language': 'id,en' }
            })
            if (res.ok) {
              const data = await res.json()
              const addr = data.display_name || `${data.address?.road || ''}, ${data.address?.suburb || ''}`
              if (addr) setForm(f => ({ ...f, lokasi: addr.trim().replace(/^,\s*/, '') }))
            }
          } catch {}
        }

        marker.on('dragend', e => {
          const p = e.target.getLatLng()
          updateCoordsAndAddress(p.lat, p.lng)
        })
        map.on('click', e => {
          marker.setLatLng(e.latlng)
          updateCoordsAndAddress(e.latlng.lat, e.latlng.lng)
        })
        mapInstanceRef.current = map
        markerRef.current = marker
      } else if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize()
      }
    }, 100)
  }, [showMapModal])

  function handleAutoDetectGPS() {
    if (!navigator.geolocation) {
      alert('Browser Anda tidak mendukung deteksi lokasi.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords
        setForm(f => ({ ...f, lat: latitude, lng: longitude }))
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`, {
            headers: { 'Accept-Language': 'id,en' }
          })
          if (res.ok) {
            const data = await res.json()
            const addr = data.display_name || `${data.address?.road || ''}, ${data.address?.suburb || ''}`
            if (addr) setForm(f => ({ ...f, lokasi: addr.trim().replace(/^,\s*/, '') }))
          }
        } catch {}
      },
      () => alert('Gagal membaca GPS. Pastikan izin lokasi aktif.'),
      { enableHighAccuracy: true, timeout: 8000 }
    )
  }

  function handleCameraCapture(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => {
      setForm(f => ({
        ...f,
        photoFile: file,
        photoPreview: ev.target.result,
        photoName: `${file.name} • ${(file.size / 1024 / 1024).toFixed(1)} MB`,
      }))
    }
    reader.readAsDataURL(file)
  }

  function handleSubmitStep1(e) {
    e.preventDefault()
    if (!form.judul.trim()) return
    if (!form.deskripsi.trim()) return
    if (!form.lokasi.trim()) return
    onNext()
  }

  const selectedKat = KATEGORI.find(k => k.id === form.kategoriId)

  return (
    <form onSubmit={handleSubmitStep1} className="report-form-layout">
      {/* Panel kiri: isi detail laporan */}
      <div className="form-panel-card">
        <div className="field-group">
          <label className="field-label">Kategori *</label>
          <select
            className="field-select"
            value={form.kategoriId}
            onChange={e => setForm(f => ({ ...f, kategoriId: e.target.value }))}
            required
          >
            {KATEGORI.map(k => <option key={k.id} value={k.id}>{k.label}</option>)}
          </select>
        </div>

        <div className="field-group">
          <label className="field-label">Judul laporan *</label>
          <input
            className="field-input"
            type="text"
            value={form.judul}
            onChange={e => setForm(f => ({ ...f, judul: e.target.value }))}
            placeholder="Contoh: Saluran tersumbat di dekat gang"
            required
          />
          <div className="field-hint">Judul singkat membantu petugas memahami masalah.</div>
        </div>

        <div className="field-group">
          <label className="field-label">Deskripsi *</label>
          <textarea
            className="field-textarea"
            rows={4}
            value={form.deskripsi}
            onChange={e => setForm(f => ({ ...f, deskripsi: e.target.value }))}
            placeholder="Jelaskan kondisi secara rinci — dampak, waktu kejadian, seberapa parah..."
            required
          />
          <div className="field-hint">Semakin detail, semakin cepat petugas merespons.</div>
        </div>

        <div className="field-group" style={{ marginBottom: 0 }}>
          <label className="field-label">Lokasi *</label>
          <div className="location-input-wrap">
            <input
              className="field-input"
              type="text"
              value={form.lokasi}
              onChange={e => setForm(f => ({ ...f, lokasi: e.target.value }))}
              placeholder="Masukkan alamat lengkap..."
              required
            />
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <div className="location-callout-box">
            <div style={{ color: '#0d9488' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </div>
            <div className="location-callout-text">
              <h5>Titik GPS terpilih</h5>
              <p>Koordinat: {form.lat.toFixed(4)}, {form.lng.toFixed(4)}</p>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                onClick={handleAutoDetectGPS}
                style={{
                  padding: '6px 12px',
                  borderRadius: 8,
                  border: '1px solid #0d9488',
                  background: '#f0fdfa',
                  color: '#0d9488',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                📍 Lokasi Saya
              </button>
              <button type="button" className="btn-ubah-lokasi" onClick={() => setShowMapModal(true)}>
                Ubah di Peta
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Panel kanan: foto & tombol lanjut */}
      <div className="photo-upload-panel">
        <div className="photo-preview-card">
          <h4>Foto Kejadian</h4>
          <div className="photo-image-display">
            {form.photoPreview ? (
              <img src={form.photoPreview} alt="Foto laporan" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', gap: 8 }}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
                <span style={{ fontSize: 13 }}>Belum ada foto</span>
              </div>
            )}
          </div>

          {form.photoFile ? (
            <div className="photo-file-meta">
              <span style={{ fontSize: 12, color: '#475569' }}>{form.photoName}</span>
              <button
                type="button"
                onClick={() => setForm(f => ({ ...f, photoFile: null, photoPreview: null, photoName: '' }))}
                style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 12 }}
              >
                Hapus foto
              </button>
            </div>
          ) : (
            <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', margin: '8px 0' }}>
              Ambil foto langsung menggunakan kamera
            </p>
          )}

          {/* Input kamera: capture="environment" untuk kamera belakang di HP */}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
            onChange={handleCameraCapture}
          />

          <button
            type="button"
            className="btn-add-photo"
            onClick={() => cameraInputRef.current?.click()}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <span>{form.photoFile ? 'Ambil Ulang Foto' : 'Buka Kamera'}</span>
          </button>
          <div className="field-hint" style={{ marginTop: 10 }}>Foto akan dianalisis sistem untuk penetapan prioritas.</div>
        </div>

        <button type="submit" className="btn-submit-review">
          <span>Tinjau Laporan</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>

      {/* Modal pilih lokasi peta */}
      {showMapModal && (
        <div className="modal-overlay active">
          <div className="modal-box">
            <div className="modal-header">
              <div className="modal-header-left">
                <div className="modal-icon-badge">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                  </svg>
                </div>
                <div>
                  <h3 className="modal-title">Tandai lokasi di peta</h3>
                  <p className="modal-subtitle">Klik atau seret penanda untuk memilih titik kejadian.</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setShowMapModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="modal-map-view" ref={mapRef} style={{ height: 320 }} />
              <div className="modal-selected-box">
                <div>
                  <div className="modal-selected-title">Titik terpilih</div>
                  <div className="modal-selected-address">{form.lat.toFixed(6)}, {form.lng.toFixed(6)}</div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <span className="modal-footer-hint">Klik peta untuk memindahkan penanda</span>
              <div className="modal-footer-actions">
                <button className="btn-modal-cancel" onClick={() => setShowMapModal(false)}>Batal</button>
                <button className="btn-modal-use" onClick={() => setShowMapModal(false)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Gunakan Lokasi Ini
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </form>
  )
}

// ─── Step 2: Ringkasan / Preview ─────────────────────────────────────────────
function Step2Preview({ form, onBack, onNext }) {
  const kat = KATEGORI.find(k => k.id === form.kategoriId)
  const shortDraft = `SW-DRAFT-${Math.floor(Math.random() * 9000 + 1000)}`

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      {/* Header card */}
      <div style={{
        background: '#fff',
        borderRadius: 16,
        padding: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        marginBottom: 16,
        borderLeft: '4px solid #0d9488',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#64748b' }}>{shortDraft}</span>
          <span style={{ padding: '4px 12px', borderRadius: 20, background: '#e8f6f4', color: '#0d9488', fontSize: 12, fontWeight: 700 }}>
            Draf — Belum dikirim
          </span>
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 8 }}>{form.judul}</h2>

        <div style={{ display: 'flex', gap: 16, fontSize: 13, color: '#64748b', marginBottom: 16, flexWrap: 'wrap' }}>
          <span>📁 {kat?.label || '—'}</span>
          <span>📍 {form.lokasi}</span>
          <span>🗺 {form.lat.toFixed(4)}, {form.lng.toFixed(4)}</span>
        </div>

        <div style={{ background: '#f8fafc', borderRadius: 10, padding: '14px 16px', fontSize: 14, color: '#475569', lineHeight: 1.7 }}>
          {form.deskripsi}
        </div>
      </div>

      {/* Foto preview */}
      <div style={{
        background: '#fff',
        borderRadius: 16,
        padding: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        marginBottom: 16,
      }}>
        <h4 style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginBottom: 12 }}>Foto Kejadian</h4>
        {form.photoPreview ? (
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <img
              src={form.photoPreview}
              alt="Foto laporan"
              style={{ width: 200, height: 140, objectFit: 'cover', borderRadius: 10 }}
            />
            <div style={{ fontSize: 13, color: '#64748b' }}>
              <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: 4 }}>{form.photoName}</div>
              <div>Foto akan disertakan bersama laporan.</div>
            </div>
          </div>
        ) : (
          <div style={{ fontSize: 13, color: '#94a3b8', fontStyle: 'italic' }}>
            Tidak ada foto yang disertakan.
          </div>
        )}
      </div>

      {/* Info AI */}
      <div style={{
        background: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: 12,
        padding: '14px 16px',
        marginBottom: 24,
        display: 'flex',
        gap: 12,
        alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: 20 }}>⚡</span>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#15803d', marginBottom: 2 }}>Analisis prioritas otomatis</div>
          <div style={{ fontSize: 13, color: '#166534' }}>
            Sistem AI akan menganalisis laporan Anda setelah dikirim untuk menentukan tingkat prioritas penanganan secara otomatis.
          </div>
        </div>
      </div>

      {/* Tombol navigasi */}
      <div style={{ display: 'flex', gap: 12 }}>
        <button
          type="button"
          onClick={onBack}
          style={{
            flex: 1, padding: '13px', borderRadius: 12, border: '1px solid #e2e8f0',
            background: '#f8fafc', color: '#475569', fontSize: 15, fontWeight: 600, cursor: 'pointer',
          }}
        >
          ← Edit Laporan
        </button>
        <button
          type="button"
          onClick={onNext}
          className="btn-submit-review"
          style={{ flex: 2 }}
        >
          <span>Konfirmasi &amp; Kirim</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>
    </div>
  )
}

// ─── Step 3: Konfirmasi Kirim ─────────────────────────────────────────────────
function Step3Konfirmasi({ form, onBack, onSubmit, submitting }) {
  const kat = KATEGORI.find(k => k.id === form.kategoriId)

  return (
    <div style={{ maxWidth: 540, margin: '0 auto' }}>
      <div style={{
        background: '#fff',
        borderRadius: 16,
        padding: 32,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        textAlign: 'center',
        marginBottom: 20,
      }}>
        {/* Ikon konfirmasi */}
        <div style={{
          width: 72, height: 72, borderRadius: '50%', background: '#e8f6f4',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 20px',
        }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.49 2 2 0 0 1 3.6 1.27h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.91a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.73 16.92z" />
          </svg>
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 8 }}>
          Kirim laporan ini?
        </h2>
        <p style={{ fontSize: 14, color: '#64748b', lineHeight: 1.6, marginBottom: 24 }}>
          Laporan Anda akan diterima oleh petugas dan dianalisis sistem AI untuk penetapan prioritas. Pastikan semua informasi sudah benar.
        </p>

        {/* Ringkasan singkat */}
        <div style={{
          background: '#f8fafc', borderRadius: 12, padding: '16px 20px',
          textAlign: 'left', marginBottom: 24,
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 20px', fontSize: 13 }}>
            <div>
              <div style={{ color: '#94a3b8', marginBottom: 2 }}>Judul</div>
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{form.judul}</div>
            </div>
            <div>
              <div style={{ color: '#94a3b8', marginBottom: 2 }}>Kategori</div>
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{kat?.label || '—'}</div>
            </div>
            <div>
              <div style={{ color: '#94a3b8', marginBottom: 2 }}>Lokasi</div>
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{form.lokasi}</div>
            </div>
            <div>
              <div style={{ color: '#94a3b8', marginBottom: 2 }}>Foto</div>
              <div style={{ fontWeight: 600, color: form.photoFile ? '#16a34a' : '#94a3b8' }}>
                {form.photoFile ? '✓ Disertakan' : 'Tidak ada'}
              </div>
            </div>
          </div>
        </div>

        {/* Tombol aksi */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="button"
            onClick={onBack}
            disabled={submitting}
            style={{
              flex: 1, padding: '13px', borderRadius: 12, border: '1px solid #e2e8f0',
              background: '#f8fafc', color: '#475569', fontSize: 15, fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer', opacity: submitting ? 0.5 : 1,
            }}
          >
            ← Kembali
          </button>
          <button
            type="button"
            onClick={onSubmit}
            disabled={submitting}
            className="btn-submit-review"
            style={{ flex: 2, opacity: submitting ? 0.8 : 1 }}
          >
            {submitting ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                <span>Mengirim...</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
                <span>Ya, Kirim Laporan</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', lineHeight: 1.6 }}>
        Dengan mengirim laporan, Anda menyatakan bahwa informasi yang diberikan akurat dan dapat dipertanggungjawabkan.
      </p>
    </div>
  )
}

// ─── Step 4: Sukses ───────────────────────────────────────────────────────────
function StepSukses({ laporanId, onNavigate }) {
  return (
    <div style={{ maxWidth: 480, margin: '0 auto', textAlign: 'center' }}>
      <div style={{
        background: '#fff', borderRadius: 20, padding: 40,
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      }}>
        <div style={{
          width: 80, height: 80, borderRadius: '50%', background: '#e8f6f4',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 24px',
        }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', marginBottom: 8 }}>
          Laporan berhasil dikirim!
        </h2>
        <p style={{ fontSize: 14, color: '#64748b', lineHeight: 1.7, marginBottom: 8 }}>
          Laporan Anda telah diterima dan sedang menunggu analisis sistem.
        </p>
        {laporanId && (
          <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 24 }}>
            ID: SW-{typeof laporanId === 'string' ? laporanId.substring(0, 8).toUpperCase() : laporanId}
          </p>
        )}
        <div style={{ display: 'flex', gap: 12, flexDirection: 'column' }}>
          <button
            onClick={() => onNavigate(`/detail-laporan?id=${laporanId}`)}
            className="btn-submit-review"
          >
            Lihat Detail Laporan
          </button>
          <button
            onClick={() => onNavigate('/laporan-saya')}
            style={{
              padding: '13px', borderRadius: 12, border: '1px solid #e2e8f0',
              background: '#f8fafc', color: '#475569', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}
          >
            Ke Laporan Saya
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function BuatLaporanPage() {
  const navigate = useNavigate()
  const token = localStorage.getItem('siagawarga_token')
  const [step, setStep] = useState(1) // 1, 2, 3, 'sukses'
  const [submitting, setSubmitting] = useState(false)
  const [authLoading, setAuthLoading] = useState(true)
  const [userName, setUserName] = useState('')
  const [userInitials, setUserInitials] = useState('')

  const [form, setForm] = useState({
    judul: '',
    deskripsi: '',
    kategoriId: KATEGORI[0].id,
    lokasi: '',
    lat: -6.4212,
    lng: 106.8501,
    photoFile: null,
    photoPreview: null,
    photoName: '',
  })

  useEffect(() => {
    if (!token) { navigate('/login'); return }
    const storedRole = (localStorage.getItem('siagawarga_role') || '').toUpperCase()
    if (storedRole === 'PETUGAS' || storedRole === 'ADMIN') {
      navigate('/dashboard-petugas', { replace: true })
      return
    }

    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(u => {
        if (!u) return
        const peran = (u.peran || '').toUpperCase()
        if (peran === 'PETUGAS' || peran === 'ADMIN') {
          navigate('/dashboard-petugas', { replace: true })
          return
        }
        if (u.nama) {
          setUserName(u.nama)
          setUserInitials(u.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase())
        }
      })
      .catch(() => {})
      .finally(() => setAuthLoading(false))
  }, [])


  async function handleSubmit() {
    if (!token) { navigate('/login'); return }
    setSubmitting(true)
    try {
      const payload = {
        judul: form.judul,
        deskripsi: form.deskripsi,
        kategori_id: form.kategoriId,
        alamat_lokasi: form.lokasi,
        latitude: form.lat,
        longitude: form.lng,
        foto_urls: [],
      }
      const res = await fetch(`${API_BASE}/laporan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        const data = await res.json()
        setLaporanId(data.id)
        setStep('sukses')
      } else {
        const err = await res.json().catch(() => ({}))
        const msg = err.detail
          ? (Array.isArray(err.detail) ? err.detail.map(d => d.msg || d).join(', ') : err.detail)
          : 'Gagal mengirim laporan.'
        alert(`⚠️ ${msg}`)
      }
    } catch {
      alert('⚠️ Kesalahan koneksi. Pastikan server aktif.')
    } finally {
      setSubmitting(false)
    }
  }

  const STEP_LABELS = ['Isi Laporan', 'Tinjau', 'Konfirmasi']

  if (authLoading) {
    return (
      <div className="app-layout">
        <Sidebar role="warga" />
        <main className="app-main">
          <Topbar roleLabel="Layanan Warga" userInitials="" />
          <div className="app-content">
            <LoadingSpinner size={40} message="Menyiapkan formulir laporan..." fullPage />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <Sidebar role="warga" />
      <main className="app-main">
        <Topbar roleLabel="Layanan Warga" userInitials={userInitials} />
        <div className="app-content">

          {/* Back link (sembunyikan di step sukses) */}
          {step !== 'sukses' && (
            <Link to="/beranda" className="back-link">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
              </svg>
              <span>Kembali ke beranda</span>
            </Link>
          )}

          <h1 className="greeting-title" style={{ fontSize: 28, marginBottom: 4 }}>
            {step === 'sukses' ? 'Laporan Terkirim' : 'Buat Laporan'}
          </h1>
          <p style={{ fontSize: 14, color: '#64748b', marginBottom: 20 }}>
            {step === 'sukses'
              ? 'Terima kasih telah berkontribusi untuk lingkungan yang lebih baik.'
              : 'Detailkan masalah yang Anda temukan di sekitar Anda.'}
          </p>

          {/* Stepper (sembunyikan di sukses) */}
          {step !== 'sukses' && (
            <>
              <div className="stepper-container" style={{ marginBottom: 8 }}>
                {STEP_LABELS.map((label, i) => {
                  const num = i + 1
                  const isActive = step === num
                  const isDone = typeof step === 'number' && step > num
                  return (
                    <div key={label} className="stepper-item">
                      <div className={`stepper-bar${isActive || isDone ? ' active' : ''}`} />
                      <div className={`stepper-label${isActive ? ' active' : ''}`} style={{ color: isDone ? '#0d9488' : undefined }}>
                        {isDone ? '✓ ' : `${num}. `}{label}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="draf-bar-info" style={{ marginBottom: 20 }}>
                <span>Langkah {step} dari 3</span>
                <span className="draf-user-name">{userName}</span>
              </div>
            </>
          )}

          {/* Step content */}
          {step === 1 && (
            <Step1Form
              form={form}
              setForm={setForm}
              onNext={() => setStep(2)}
              userName={userName}
              userInitials={userInitials}
            />
          )}
          {step === 2 && (
            <Step2Preview
              form={form}
              onBack={() => setStep(1)}
              onNext={() => setStep(3)}
            />
          )}
          {step === 3 && (
            <Step3Konfirmasi
              form={form}
              onBack={() => setStep(2)}
              onSubmit={handleSubmit}
              submitting={submitting}
            />
          )}
          {step === 'sukses' && (
            <StepSukses
              laporanId={laporanId}
              onNavigate={navigate}
            />
          )}

        </div>
      </main>

      {/* Spin animation untuk loading */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
