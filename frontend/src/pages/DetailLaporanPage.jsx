import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'
import 'leaflet/dist/leaflet.css'

const STATUS_LABEL = {
  DIKIRIM: 'Laporan Dikirim',
  DIVERIFIKASI: 'Diverifikasi',
  DIPROSES: 'Sedang Diproses',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
}

export default function DetailLaporanPage() {
  const [searchParams] = useSearchParams()
  const id = searchParams.get('id')
  const { userRole: authRole, userInitials: authInitials, token } = useAuth()
  const storedRole = (localStorage.getItem('siagawarga_role') || authRole || '').toUpperCase()
  const isPetugas = storedRole === 'PETUGAS' || storedRole === 'ADMIN'
  const storedInitials = localStorage.getItem('siagawarga_initials')

  const [report, setReport] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [userInitials, setUserInitials] = useState(authInitials || storedInitials || (isPetugas ? 'PT' : 'SW'))
  const [userRole, setUserRole] = useState(storedRole)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)


  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        if (token) {
          const meRes = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          if (meRes.ok) {
            const u = await meRes.json()
            if (u.nama) setUserInitials(u.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase())
            setUserRole((u.peran || 'WARGA').toUpperCase())
          }
        }

        if (!id) { setNotFound(true); setLoading(false); return }

        const headers = token ? { Authorization: `Bearer ${token}` } : {}

        const statusRes = await fetch(`${API_BASE}/laporan/${id}/status`, { headers })
        let currentData = null
        if (statusRes.ok) {
          const track = await statusRes.json()
          setTimeline(track.timeline || [])
          currentData = {
            id: track.id,
            judul: track.judul,
            status: track.status_terkini,
            dibuat_pada: track.dibuat_pada,
          }
        }

        const detailEndpoints = [
          `${API_BASE}/petugas/laporan/${id}`,
          `${API_BASE}/laporan/${id}`,
        ]
        for (const ep of detailEndpoints) {
          try {
            const r = await fetch(ep, { headers })
            if (r.ok) {
              const d = await r.json()
              currentData = { ...currentData, ...d }
              if (d.riwayat_status && (!currentData.timeline || currentData.timeline.length === 0)) {
                setTimeline(d.riwayat_status)
              }
              break
            }
          } catch {}
        }

        if (currentData) {
          setReport(currentData)
        } else {
          setNotFound(true)
        }
      } catch (err) {
        console.error(err)
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  useEffect(() => {
    if (!report) return
    const lat = parseFloat(report.latitude || report.lat || 0)
    const lng = parseFloat(report.longitude || report.lng || 0)
    if (!lat && !lng) return

    let map = null
    const timer = setTimeout(async () => {
      const container = document.getElementById('detailMapContainer')
      if (!container) return
      const L = (await import('leaflet')).default
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })
      map = L.map(container, { zoomControl: false }).setView([lat, lng], 16)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
      }).addTo(map)
      L.marker([lat, lng]).addTo(map)
    }, 150)

    return () => {
      clearTimeout(timer)
      if (map) map.remove()
    }
  }, [report])

  const sidebarRole = userRole === 'PETUGAS' || userRole === 'ADMIN' ? 'petugas' : 'warga'
  const backLink = sidebarRole === 'petugas' ? '/dashboard-petugas' : '/laporan-saya'

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar role={sidebarRole} />
        <main className="app-main">
          <Topbar
            roleLabel={sidebarRole === 'petugas' ? 'Dashboard Petugas' : 'Layanan Warga'}
            userInitials={userInitials || (isPetugas ? 'PT' : 'SW')}
            avatarBg={isPetugas ? '#1e3a5f' : undefined}
          />
          <div className="app-content">
            <LoadingSpinner size={40} message="Mengambil rincian laporan..." fullPage />
          </div>
        </main>
      </div>
    )
  }

  if (notFound || !report) {
    return (
      <div className="app-layout">
        <Sidebar role={sidebarRole} />
        <main className="app-main">
          <Topbar
            roleLabel={sidebarRole === 'petugas' ? 'Dashboard Petugas' : 'Layanan Warga'}
            userInitials={userInitials || (isPetugas ? 'PT' : 'SW')}
            avatarBg={isPetugas ? '#1e3a5f' : undefined}
          />
          <div className="app-content" style={{padding:60,textAlign:'center'}}>
            <p style={{color:'#94a3b8',fontSize:16,marginBottom:12}}>Laporan tidak ditemukan.</p>
            <Link to={backLink} style={{color:'#0d9488',fontWeight:700}}>Kembali</Link>
          </div>
        </main>
      </div>
    )
  }

  const shortId = typeof report.id === 'string' ? report.id.substring(0, 8).toUpperCase() : String(report.id)
  const code = `SW-${shortId}`
  const st = (report.status || 'DIKIRIM').toUpperCase()
  const prio = (report.kategori_prioritas || report.severity || '').toUpperCase()
  const isUrgent = prio === 'P1' || prio === 'TINGGI'
  const namaKat = report.kategori
    ? (typeof report.kategori === 'object' ? report.kategori.nama : report.kategori)
    : 'Umum'
  const rawDate = report.dibuat_pada || report.created_at
  const dateStr = rawDate
    ? new Date(rawDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'Baru saja'

  return (
    <div className="app-layout">
      <Sidebar role={sidebarRole} />
      <main className="app-main">
        <Topbar
          roleLabel={sidebarRole === 'petugas' ? 'Dashboard Petugas' : 'Layanan Warga'}
          userInitials={userInitials || (isPetugas ? 'PT' : 'SW')}
          avatarBg={isPetugas ? '#1e3a5f' : undefined}
        />

        <div className="app-content">
          <Link to={backLink} className="back-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
            </svg>
            <span>Kembali</span>
          </Link>

          <div className="detail-layout-grid">
            <div className="detail-left-col">
              <div className="detail-header-card">
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:12}}>
                  <div>
                    <div style={{fontSize:12,fontWeight:600,color:'#64748b',marginBottom:6}}>{code}</div>
                    <h1 style={{fontSize:22,fontWeight:800,color:'#0f172a',margin:0}}>{report.judul}</h1>
                  </div>
                  <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
                    <span className={`pill-badge ${isUrgent ? 'badge-urgent' : 'badge-low'}`}>
                      <span className="pill-dot"/><span>{isUrgent ? 'Urgent (P1)' : (prio || 'Normal')}</span>
                    </span>
                    <span className={`pill-badge ${st === 'SELESAI' ? 'badge-in-progress' : st === 'DITOLAK' ? 'badge-urgent' : 'badge-waiting'}`}>
                      <span className="pill-dot"/><span>{STATUS_LABEL[st] || st}</span>
                    </span>
                  </div>
                </div>
                <div style={{marginTop:16,display:'flex',gap:24,flexWrap:'wrap',fontSize:13,color:'#64748b'}}>
                  <span>📁 {namaKat}</span>
                  <span>📅 {dateStr}</span>
                  {report.alamat_lokasi && <span>📍 {report.alamat_lokasi}</span>}
                  {report.skor_prioritas && <span>⚡ Skor: {report.skor_prioritas}</span>}
                </div>
              </div>

              {report.deskripsi && (
                <div className="detail-section-card">
                  <h3 style={{fontSize:15,fontWeight:700,marginBottom:10,color:'#0f172a'}}>Deskripsi</h3>
                  <p style={{fontSize:14,color:'#475569',lineHeight:1.7}}>{report.deskripsi}</p>
                </div>
              )}

              {(report.latitude || report.lat) && (
                <div className="detail-section-card">
                  <h3 style={{fontSize:15,fontWeight:700,marginBottom:10,color:'#0f172a'}}>Lokasi Kejadian</h3>
                  <div id="detailMapContainer" style={{height:240,borderRadius:12,overflow:'hidden'}} />
                  <p style={{fontSize:12,color:'#94a3b8',marginTop:8}}>
                    {parseFloat(report.latitude || report.lat).toFixed(6)}, {parseFloat(report.longitude || report.lng).toFixed(6)}
                  </p>
                </div>
              )}

              {report.foto_urls && report.foto_urls.length > 0 && (
                <div className="detail-section-card">
                  <h3 style={{fontSize:15,fontWeight:700,marginBottom:10,color:'#0f172a'}}>Foto Laporan</h3>
                  <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
                    {report.foto_urls.map((url, i) => (
                      <img key={i} src={url} alt={`Foto ${i+1}`} style={{width:160,height:120,objectFit:'cover',borderRadius:8}} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="detail-right-col">
              <div className="detail-timeline-card">
                <h3 style={{fontSize:15,fontWeight:700,marginBottom:16,color:'#0f172a'}}>Riwayat Status</h3>
                {timeline.length === 0 ? (
                  <div style={{fontSize:13,color:'#94a3b8',padding:'20px 0',textAlign:'center'}}>
                    Belum ada riwayat status.
                  </div>
                ) : timeline.map((t, i) => {
                  const tDate = t.diubah_pada || t.created_at
                  const tDateStr = tDate
                    ? new Date(tDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
                    : ''
                  return (
                    <div key={i} className="timeline-item" style={{
                      display:'flex',gap:12,marginBottom:20,
                      paddingBottom:20,borderBottom: i < timeline.length-1 ? '1px solid #f1f5f9' : 'none'
                    }}>
                      <div style={{
                        width:32,height:32,borderRadius:'50%',background: i === 0 ? '#0d9488' : '#e2e8f0',
                        display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,marginTop:2
                      }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={i === 0 ? '#fff' : '#94a3b8'} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      </div>
                      <div>
                        <div style={{fontSize:13,fontWeight:700,color:'#0f172a'}}>
                          {STATUS_LABEL[t.status?.toUpperCase()] || t.status}
                        </div>
                        {t.catatan && <p style={{fontSize:13,color:'#475569',marginTop:4}}>{t.catatan}</p>}
                        {tDateStr && <div style={{fontSize:12,color:'#94a3b8',marginTop:4}}>{tDateStr}</div>}
                      </div>
                    </div>
                  )
                })}
              </div>

              {report.ai_klasifikasi && (
                <div className="detail-section-card" style={{marginTop:16}}>
                  <h3 style={{fontSize:15,fontWeight:700,marginBottom:12,color:'#0f172a'}}>⚡ Analisis AI</h3>
                  <div style={{fontSize:13,color:'#475569'}}>
                    {report.ai_klasifikasi.kategori && (
                      <div style={{marginBottom:8}}>
                        <strong>Kategori:</strong> {report.ai_klasifikasi.kategori}
                      </div>
                    )}
                    {report.ai_klasifikasi.confidence_score && (
                      <div style={{marginBottom:8}}>
                        <strong>Keyakinan:</strong> {Math.round(report.ai_klasifikasi.confidence_score * 100)}%
                      </div>
                    )}
                    {report.ai_klasifikasi.penjelasan && (
                      <div><strong>Penjelasan:</strong> {report.ai_klasifikasi.penjelasan}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
