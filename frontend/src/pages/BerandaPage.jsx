import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner, SkeletonBox } from '../components/LoadingSpinner'
import { API_BASE } from '../config'

const STATUS_LABEL = {
  DIKIRIM: 'Menunggu verifikasi',
  MENUNGGU: 'Menunggu',
  DIPROSES: 'Ditangani',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
}

const STATUS_CLASS = {
  DIKIRIM: 'badge-waiting',
  MENUNGGU: 'badge-waiting',
  DIPROSES: 'badge-in-progress',
  SELESAI: 'badge-in-progress',
  DITOLAK: 'badge-urgent',
}

export default function BerandaPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [reports, setReports] = useState([])
  const [counts, setCounts] = useState({ total: 0, aktif: 0, selesai: 0 })
  const [loading, setLoading] = useState(true)
  const token = localStorage.getItem('siagawarga_token')

  useEffect(() => {
    async function load() {
      const storedRole = (localStorage.getItem('siagawarga_role') || '').toUpperCase()
      if (storedRole === 'PETUGAS' || storedRole === 'ADMIN') {
        navigate('/dashboard-petugas', { replace: true })
        return
      }

      setLoading(true)
      try {
        if (token) {
          const meRes = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          if (meRes.ok) {
            const u = await meRes.json()
            const peran = (u.peran || '').toUpperCase()
            if (peran === 'PETUGAS' || peran === 'ADMIN') {
              navigate('/dashboard-petugas', { replace: true })
              return
            }
            setUser(u)
          }
        }


        let list = []
        if (token) {
          const r = await fetch(`${API_BASE}/laporan/saya`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          if (r.ok) {
            const data = await r.json()
            list = Array.isArray(data) ? data : (data.items || [])
          }
        }

        setReports(list.slice(0, 4))
        const total = list.length
        const aktif = list.filter(r => {
          const s = (r.status || '').toUpperCase()
          return s !== 'SELESAI' && s !== 'DITOLAK'
        }).length
        const selesai = list.filter(r => (r.status || '').toUpperCase() === 'SELESAI').length
        setCounts({ total, aktif, selesai })
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const initials = user?.nama
    ? user.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : ''
  const firstName = user?.nama ? user.nama.split(' ')[0] : ''

  if (loading && !user) {
    return (
      <div className="app-layout">
        <Sidebar role="warga" />
        <main className="app-main">
          <Topbar roleLabel="Layanan Warga" userInitials="" />
          <div className="app-content">
            <LoadingSpinner size={40} message="Menghubungkan ke layanan SiagaWarga..." fullPage />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <Sidebar role="warga" />
      <main className="app-main">
        <Topbar roleLabel="Layanan Warga" userInitials={initials} />
        <div className="app-content">
          <section className="greeting-section">
            <div className="greeting-location">Wilayah Anda</div>
            <h1 className="greeting-title">
              Selamat datang, {firstName || 'Warga'}
            </h1>
          </section>

          <div className="banner-dark-card">
            <div>
              <h2 className="banner-dark-title">Ada masalah di sekitar Anda?</h2>
              <p className="banner-dark-desc">Laporkan dengan lokasi dan foto.</p>
            </div>
            <Link to="/buat-laporan" className="btn-teal-action">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              <span>Buat laporan</span>
            </Link>
          </div>

          <div className="section-bar">
            <h2 className="section-bar-title">Laporan Anda</h2>
            <Link to="/laporan-saya" className="btn-pill-outline">Lihat semua</Link>
          </div>

          <div className="stat-triplet-grid">
            <div className="stat-triplet-card">
              <div className="stat-triplet-number">
                {loading ? <SkeletonBox width={50} height={32} style={{ margin: '0 auto' }} /> : counts.total}
              </div>
              <div className="stat-triplet-label">Total laporan</div>
            </div>
            <div className="stat-triplet-card">
              <div className="stat-triplet-number">
                {loading ? <SkeletonBox width={50} height={32} style={{ margin: '0 auto' }} /> : counts.aktif}
              </div>
              <div className="stat-triplet-label">Masih aktif</div>
            </div>
            <div className="stat-triplet-card">
              <div className="stat-triplet-number">
                {loading ? <SkeletonBox width={50} height={32} style={{ margin: '0 auto' }} /> : counts.selesai}
              </div>
              <div className="stat-triplet-label">Selesai</div>
            </div>
          </div>

          <div className="section-bar" style={{marginTop:12}}>
            <h2 className="section-bar-title" style={{fontSize:20}}>Aktivitas terbaru</h2>
          </div>

          {loading ? (
            <LoadingSpinner message="Mengambil aktivitas laporan terbaru..." />
          ) : (
            <div className="activities-twin-grid">
              {reports.length === 0 ? (
                <div style={{gridColumn:'1/-1',padding:40,textAlign:'center',color:'#94a3b8',fontSize:14}}>
                  Belum ada laporan.{' '}
                  <Link to="/buat-laporan" style={{color:'#0d9488',fontWeight:700}}>Buat laporan pertama Anda.</Link>
                </div>
              ) : reports.map(r => {
                const shortId = typeof r.id === 'string' ? r.id.substring(0, 8).toUpperCase() : String(r.id)
                const code = `SW-${shortId}`
                const st = (r.status || 'DIKIRIM').toUpperCase()
                const prio = (r.kategori_prioritas || r.severity || '').toUpperCase()
                const isUrgent = prio === 'P1' || prio === 'TINGGI'
                const rawDate = r.dibuat_pada || r.created_at
                const dateStr = rawDate
                  ? new Date(rawDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
                  : 'Baru saja'
                const namaKat = r.kategori
                  ? (typeof r.kategori === 'object' ? r.kategori.nama : r.kategori)
                  : 'Umum'
                const alamat = r.alamat_lokasi || r.lokasi_deskripsi || 'Wilayah pelaporan'

                return (
                  <Link key={r.id} to={`/detail-laporan?id=${r.id}`} className="activity-report-box">
                    <div>
                      <div className="activity-header-line">
                        <span className="activity-code">{code}</span>
                        <span className="activity-chevron">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="9 18 15 12 9 6"/>
                          </svg>
                        </span>
                      </div>
                      <h3 className="activity-title">{r.judul}</h3>
                      <div className="activity-location">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        <span>{alamat}</span>
                      </div>
                      <div className="activity-pills">
                        <span className={`pill-badge ${isUrgent ? 'badge-urgent' : 'badge-low'}`}>
                          <span className="pill-dot"/><span>{isUrgent ? 'Urgent (P1)' : (prio || 'Normal')}</span>
                        </span>
                        <span className={`pill-badge ${STATUS_CLASS[st] || 'badge-waiting'}`}>
                          <span className="pill-dot"/><span>{STATUS_LABEL[st] || st}</span>
                        </span>
                      </div>
                    </div>
                    <div className="activity-footer-text">{dateStr} • {namaKat}</div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
