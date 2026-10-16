import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LocateFixed, MapPin, ExternalLink, CheckCircle, Clock } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner, SkeletonBox } from '../components/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'
import 'leaflet/dist/leaflet.css'

const PRIO_COLOR = {
  P1: '#dc2626',
  P2: '#f97316',
  P3: '#eab308',
  P4: '#22c55e',
}

const STATUS_LABEL = {
  DIKIRIM: 'Dikirim',
  DIVERIFIKASI: 'Diverifikasi',
  DIPROSES: 'Sedang Diproses',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
}

export default function PetaPage() {
  const navigate = useNavigate()
  const { userInitials, userRole, token } = useAuth()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedReport, setSelectedReport] = useState(null)
  const [userLoc, setUserLoc] = useState(null)
  const [userAddress, setUserAddress] = useState('')
  const [locating, setLocating] = useState(false)
  const [locError, setLocError] = useState('')
  const [updating, setUpdating] = useState(false)
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersLayerRef = useRef(null)
  const userMarkerRef = useRef(null)

  const storedRole = (localStorage.getItem('siagawarga_role') || userRole || '').toUpperCase()
  const isPetugas = storedRole === 'PETUGAS' || storedRole === 'ADMIN'
  const storedInitials = localStorage.getItem('siagawarga_initials')
  const displayInitials = userInitials || storedInitials || (isPetugas ? 'PT' : 'SW')

  // Fetch daftar titik laporan
  async function loadReports() {
    setLoading(true)
    try {
      const r = await fetch(`${API_BASE}/spasial/prioritas?limit=100`)
      if (r.ok) {
        const data = await r.json()
        setReports(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('Gagal mengambil laporan spasial:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  // Fungsi reverse geocoding via OpenStreetMap Nominatim
  async function reverseGeocode(lat, lng) {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`, {
        headers: { 'Accept-Language': 'id,en' }
      })
      if (res.ok) {
        const data = await res.json()
        const addr = data.display_name || `${data.address?.road || ''}, ${data.address?.suburb || data.address?.city || ''}`
        setUserAddress(addr.trim().replace(/^,\s*/, ''))
      }
    } catch {
      setUserAddress(`${lat.toFixed(5)}, ${lng.toFixed(5)}`)
    }
  }

  // Fungsi deteksi GPS saat ini dan redirect kamera peta
  async function handleGetCurrentLocation() {
    if (!navigator.geolocation) {
      setLocError('Browser Anda tidak mendukung deteksi lokasi (Geolocation).')
      return
    }

    setLocating(true)
    setLocError('')

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords
        setUserLoc({ lat: latitude, lng: longitude })
        setLocating(false)

        await reverseGeocode(latitude, longitude)

        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([latitude, longitude], 16, { animate: true, duration: 1.5 })

          const L = (await import('leaflet')).default
          if (userMarkerRef.current) {
            userMarkerRef.current.setLatLng([latitude, longitude])
          } else {
            const userIcon = L.divIcon({
              className: '',
              html: `<div style="width:20px;height:20px;border-radius:50%;background:#0284c7;border:3px solid white;box-shadow:0 0 10px rgba(2,132,199,0.7);animation:sw-pulse 2s infinite"></div>`,
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            })
            userMarkerRef.current = L.marker([latitude, longitude], { icon: userIcon })
              .addTo(mapInstanceRef.current)
              .bindPopup('<b>📍 Lokasi Anda Saat Ini</b>')
              .openPopup()
          }
        }
      },
      (err) => {
        setLocating(false)
        console.warn('Geolocation error:', err)
        setLocError('Gagal mendeteksi lokasi GPS. Pastikan izin akses lokasi diizinkan di browser.')
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  // Aksi cepat petugas: update status laporan langsung dari peta
  async function handleQuickStatusUpdate(laporanId, statusTarget) {
    if (!token) return
    setUpdating(true)
    try {
      const res = await fetch(`${API_BASE}/petugas/laporan/${laporanId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          status_baru: statusTarget,
          catatan: `Status diperbarui langsung dari peta operasional menjadi ${statusTarget}.`,
        }),
      })
      if (res.ok) {
        alert(`✅ Status laporan berhasil diperbarui ke ${statusTarget}!`)
        setSelectedReport(prev => prev ? { ...prev, status: statusTarget } : null)
        loadReports()
      } else {
        const err = await res.json().catch(() => ({}))
        alert(`⚠️ ${err.detail || 'Gagal mengubah status.'}`)
      }
    } catch {
      alert('⚠️ Kesalahan koneksi jaringan.')
    } finally {
      setUpdating(false)
    }
  }

  // Inisialisasi peta Leaflet & Layer Group untuk markers
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    async function initMap() {
      const L = (await import('leaflet')).default
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      const defaultCenter = [-6.4212, 106.8501]
      const map = L.map(mapRef.current).setView(defaultCenter, 13)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(map)

      const markersLayer = L.layerGroup().addTo(map)
      markersLayerRef.current = markersLayer
      mapInstanceRef.current = map

      if (navigator.geolocation && !userLoc) {
        handleGetCurrentLocation()
      }
    }

    initMap()
  }, [])

  // Render & sinkronkan markers setiap kali data `reports` berubah
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return

    async function updateMarkers() {
      const L = (await import('leaflet')).default
      markersLayerRef.current.clearLayers()

      reports.forEach(r => {
        const lat = parseFloat(r.latitude || r.lat)
        const lng = parseFloat(r.longitude || r.lng)
        if (!lat || !lng) return

        const prio = (r.kategori_prioritas || r.severity || 'P4').toUpperCase()
        const color = PRIO_COLOR[prio] || '#22c55e'
        const shortId = String(r.id).substring(0, 8).toUpperCase()
        const st = (r.status || 'DIKIRIM').toUpperCase()
        const statusText = STATUS_LABEL[st] || st
        const alamat = r.alamat_lokasi || r.lokasi_deskripsi || 'Lokasi tidak tersedia'

        const icon = L.divIcon({
          className: '',
          html: `<div style="width:18px;height:18px;border-radius:50%;background:${color};border:2.5px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.35);cursor:pointer;transition:transform 0.15s ease;" onmouseover="this.style.transform='scale(1.25)'" onmouseout="this.style.transform='scale(1)'"></div>`,
          iconSize: [18, 18],
          iconAnchor: [9, 9],
        })

        const marker = L.marker([lat, lng], { icon }).addTo(markersLayerRef.current)

        // Buat Popup interaktif langsung di titik pin map
        const popupContent = document.createElement('div')
        popupContent.style.minWidth = '220px'
        popupContent.style.maxWidth = '280px'
        popupContent.style.padding = '4px'
        popupContent.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'

        popupContent.innerHTML = `
          <div style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:2px">SW-${shortId}</div>
          <div style="font-size:14px;font-weight:800;color:#0f172a;line-height:1.3;margin-bottom:6px">${r.judul}</div>
          <div style="display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap">
            <span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;color:#fff;background:${color}">${prio}</span>
            <span style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px;color:#0f172a;background:#f1f5f9">${statusText}</span>
          </div>
          <div style="font-size:12px;color:#475569;margin-bottom:10px;line-height:1.4">
            📍 ${alamat}
          </div>
        `

        const actionsDiv = document.createElement('div')
        actionsDiv.style.display = 'flex'
        actionsDiv.style.flexDirection = 'column'
        actionsDiv.style.gap = '6px'

        if (isPetugas) {
          const btnGroup = document.createElement('div')
          btnGroup.style.display = 'flex'
          btnGroup.style.gap = '6px'

          if (st !== 'DIPROSES') {
            const btnProses = document.createElement('button')
            btnProses.textContent = '⚡ Tangani'
            btnProses.style.cssText = 'flex:1;padding:6px;border-radius:6px;border:none;background:#0284c7;color:#fff;font-size:11px;font-weight:700;cursor:pointer'
            btnProses.onclick = (e) => {
              e.stopPropagation()
              handleQuickStatusUpdate(r.id, 'DIPROSES')
            }
            btnGroup.appendChild(btnProses)
          }

          if (st !== 'SELESAI') {
            const btnSelesai = document.createElement('button')
            btnSelesai.textContent = '✅ Selesai'
            btnSelesai.style.cssText = 'flex:1;padding:6px;border-radius:6px;border:none;background:#16a34a;color:#fff;font-size:11px;font-weight:700;cursor:pointer'
            btnSelesai.onclick = (e) => {
              e.stopPropagation()
              handleQuickStatusUpdate(r.id, 'SELESAI')
            }
            btnGroup.appendChild(btnSelesai)
          }

          if (btnGroup.children.length > 0) {
            actionsDiv.appendChild(btnGroup)
          }
        }

        const btnDetail = document.createElement('button')
        btnDetail.textContent = '📋 Buka Detail Laporan'
        btnDetail.style.cssText = 'width:100%;padding:7px;border-radius:6px;border:1px solid #cbd5e1;background:#f8fafc;color:#0f172a;font-size:11px;font-weight:700;cursor:pointer'
        btnDetail.onclick = (e) => {
          e.stopPropagation()
          navigate(`/detail-laporan?id=${r.id}`)
        }
        actionsDiv.appendChild(btnDetail)

        popupContent.appendChild(actionsDiv)
        marker.bindPopup(popupContent, { maxWidth: 300, minWidth: 220 })

        // Event Klik Titik Peta: Langsung pilih laporan untuk panel interaktif & buka popup
        marker.on('click', () => {
          setSelectedReport(r)
          mapInstanceRef.current.panTo([lat, lng])
          marker.openPopup()
          if (window.innerWidth <= 960) {
            setTimeout(() => {
              const panel = document.getElementById('selected-report-panel')
              if (panel) {
                panel.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }
            }, 150)
          }
        })
      })
    }

    updateMarkers()
  }, [reports, isPetugas])

  const p1 = reports.filter(r => (r.kategori_prioritas || '').toUpperCase() === 'P1').length
  const p2 = reports.filter(r => (r.kategori_prioritas || '').toUpperCase() === 'P2').length
  const p3 = reports.filter(r => (r.kategori_prioritas || '').toUpperCase() === 'P3').length

  return (
    <div className="app-layout">
      <Sidebar role={isPetugas ? 'petugas' : 'warga'} />
      <main className="app-main">
        <Topbar
          roleLabel={isPetugas ? 'Dashboard Petugas' : 'Layanan Warga'}
          userInitials={displayInitials}
          avatarBg={isPetugas ? '#1e3a5f' : undefined}
        />
        <div className="app-content">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 16 }}>
            <section className="greeting-section" style={{ margin: 0 }}>
              <div className="greeting-location">
                {isPetugas ? 'Peta Operasional Wilayah Petugas' : 'Persebaran laporan aktif wilayah'}
              </div>

              <h1 className="greeting-title">Peta Laporan</h1>
            </section>

            <button
              onClick={handleGetCurrentLocation}
              disabled={locating}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '10px 18px',
                borderRadius: 10,
                border: '1px solid #0d9488',
                backgroundColor: '#e8f6f4',
                color: '#087c78',
                fontSize: 13,
                fontWeight: 700,
                cursor: locating ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <LocateFixed size={18} className={locating ? 'sw-spin' : ''} />
              <span>{locating ? 'Mendeteksi Lokasi...' : 'Lokasi Saya Sekarang'}</span>
            </button>
          </div>

          {userAddress && (
            <div style={{
              background: '#f0fdfa',
              border: '1px solid #99f6e4',
              borderRadius: 12,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: 13,
              color: '#0f766e',
              marginBottom: 16,
            }}>
              <MapPin size={18} style={{ flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <strong>Lokasi saat ini:</strong> {userAddress}
              </div>
            </div>
          )}

          {locError && (
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: 12,
              padding: '12px 16px',
              fontSize: 13,
              color: '#b91c1c',
              marginBottom: 16,
            }}>
              ⚠️ {locError}
            </div>
          )}

          <div className="stat-triplet-grid" style={{ marginBottom: 16 }}>
            <div className="stat-triplet-card" style={{ borderTop: '3px solid #dc2626' }}>
              <div className="stat-triplet-number" style={{ color: '#dc2626' }}>
                {loading ? <SkeletonBox width={40} height={32} style={{ margin: '0 auto' }} /> : p1}
              </div>
              <div className="stat-triplet-label">Prioritas P1</div>
            </div>
            <div className="stat-triplet-card" style={{ borderTop: '3px solid #f97316' }}>
              <div className="stat-triplet-number" style={{ color: '#f97316' }}>
                {loading ? <SkeletonBox width={40} height={32} style={{ margin: '0 auto' }} /> : p2}
              </div>
              <div className="stat-triplet-label">Prioritas P2</div>
            </div>
            <div className="stat-triplet-card" style={{ borderTop: '3px solid #eab308' }}>
              <div className="stat-triplet-number" style={{ color: '#eab308' }}>
                {loading ? <SkeletonBox width={40} height={32} style={{ margin: '0 auto' }} /> : p3}
              </div>
              <div className="stat-triplet-label">Prioritas P3</div>
            </div>
          </div>

          {/* Layout Split Peta + Panel Detail Interaktif */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: selectedReport ? '1fr 360px' : '1fr',
            gap: 16,
            alignItems: 'start',
            transition: 'grid-template-columns 0.25s ease'
          }}>
            {/* Box Canvas Peta */}
            <div style={{ background: '#fff', borderRadius: 16, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.08)', position: 'relative' }}>
              <div style={{ padding: '12px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>Legenda:</span>
                {[['P1', '#dc2626', 'Sangat Tinggi'], ['P2', '#f97316', 'Tinggi'], ['P3', '#eab308', 'Sedang'], ['P4', '#22c55e', 'Rendah']].map(([p, c, l]) => (
                  <span key={p} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#475569' }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: c, display: 'inline-block' }}></span>
                    {p} – {l}
                  </span>
                ))}
              </div>

              {loading ? (
                <div style={{ height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <LoadingSpinner size={36} message="Menyiapkan peta sebaran wilayah..." />
                </div>
              ) : (
                <div ref={mapRef} style={{ height: 520 }} />
              )}
            </div>

            {/* Panel Interaktif Saat Laporan Diklik dari Peta */}
            {selectedReport && (
              <div
                id="selected-report-panel"
                style={{
                  background: '#ffffff',
                  border: '1px solid #eaecf0',
                  borderRadius: 16,
                  padding: 20,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
                  position: 'relative',
                }}
              >

                <button
                  onClick={() => setSelectedReport(null)}
                  style={{
                    position: 'absolute', top: 12, right: 12,
                    background: '#f1f5f9', border: 'none', borderRadius: '50%',
                    width: 28, height: 28, display: 'flex', alignItems: 'center',
                    justifyContent: 'center', cursor: 'pointer', color: '#64748b'
                  }}
                  title="Tutup Panel"
                >
                  ✕
                </button>

                <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', marginBottom: 4 }}>
                  SW-{String(selectedReport.id).substring(0, 8).toUpperCase()}
                </div>

                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#0f172a', marginBottom: 8, paddingRight: 24 }}>
                  {selectedReport.judul}
                </h3>

                <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '3px 8px', borderRadius: 12, fontSize: 11, fontWeight: 700, color: '#fff',
                    backgroundColor: PRIO_COLOR[(selectedReport.kategori_prioritas || 'P4').toUpperCase()] || '#0d9488'
                  }}>
                    {selectedReport.kategori_prioritas || 'Normal'}
                  </span>
                  <span style={{
                    padding: '3px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, color: '#0f172a',
                    backgroundColor: '#f1f5f9'
                  }}>
                    {STATUS_LABEL[(selectedReport.status || '').toUpperCase()] || selectedReport.status}
                  </span>
                </div>

                <div style={{ fontSize: 13, color: '#475569', marginBottom: 16, lineHeight: 1.5 }}>
                  <p style={{ marginBottom: 6 }}>📍 {selectedReport.alamat_lokasi || 'Lokasi tidak tersedia'}</p>
                  {selectedReport.deskripsi && (
                    <p style={{ background: '#f8fafc', padding: '8px 10px', borderRadius: 8, fontSize: 12 }}>
                      {selectedReport.deskripsi}
                    </p>
                  )}
                </div>

                {/* Aksi Khusus Petugas */}
                {isPetugas && (
                  <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 14, marginBottom: 14 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', marginBottom: 8 }}>
                      Tindakan Cepat Petugas:
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => handleQuickStatusUpdate(selectedReport.id, 'DIPROSES')}
                        disabled={updating || selectedReport.status === 'DIPROSES'}
                        style={{
                          flex: 1, padding: '8px 10px', borderRadius: 8, border: 'none',
                          background: '#0284c7', color: '#fff', fontSize: 12, fontWeight: 700,
                          cursor: updating ? 'not-allowed' : 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4,
                          opacity: selectedReport.status === 'DIPROSES' ? 0.6 : 1
                        }}
                      >
                        <Clock size={14} /> Tangani
                      </button>
                      <button
                        onClick={() => handleQuickStatusUpdate(selectedReport.id, 'SELESAI')}
                        disabled={updating || selectedReport.status === 'SELESAI'}
                        style={{
                          flex: 1, padding: '8px 10px', borderRadius: 8, border: 'none',
                          background: '#16a34a', color: '#fff', fontSize: 12, fontWeight: 700,
                          cursor: updating ? 'not-allowed' : 'pointer',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4,
                          opacity: selectedReport.status === 'SELESAI' ? 0.6 : 1
                        }}
                      >
                        <CheckCircle size={14} /> Selesai
                      </button>
                    </div>
                  </div>
                )}

                {/* Tombol Lihat Rincian Lengkap */}
                <Link
                  to={`/detail-laporan?id=${selectedReport.id}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 6,
                    width: '100%',
                    padding: '10px',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                    background: '#f8fafc',
                    color: '#0f172a',
                    fontSize: 13,
                    fontWeight: 700,
                    textDecoration: 'none'
                  }}
                >
                  <span>Buka Halaman Detail</span>
                  <ExternalLink size={14} />
                </Link>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
