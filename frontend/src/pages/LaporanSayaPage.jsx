import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { API_BASE } from '../config'

export default function LaporanSayaPage() {
  const navigate = useNavigate()
  const [allReports, setAllReports] = useState([])
  const [filterTab, setFilterTab] = useState('all')
  const [search, setSearch] = useState('')
  const [userInitials, setUserInitials] = useState('')
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
            if (u.nama) setUserInitials(u.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase())
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
        if (!list.length) {
          const r = await fetch(`${API_BASE}/spasial/prioritas?limit=50`)
          if (r.ok) {
            const data = await r.json()
            list = Array.isArray(data) ? data : []
          }
        }
        setAllReports(list)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const total = allReports.length
  const aktif = allReports.filter(r => {
    const s = (r.status || '').toUpperCase()
    return s !== 'SELESAI' && s !== 'DITOLAK'
  }).length
  const selesai = allReports.filter(r => (r.status || '').toUpperCase() === 'SELESAI').length

  const filtered = allReports
    .filter(r => {
      const q = search.toLowerCase()
      if (!q) return true
      const shortId = typeof r.id === 'string' ? r.id.substring(0, 8).toLowerCase() : ''
      return (
        (r.judul || '').toLowerCase().includes(q) ||
        shortId.includes(q) ||
        (r.alamat_lokasi || '').toLowerCase().includes(q)
      )
    })
    .filter(r => {
      const s = (r.status || '').toUpperCase()
      if (filterTab === 'aktif') return s !== 'SELESAI' && s !== 'DITOLAK'
      if (filterTab === 'selesai') return s === 'SELESAI'
      return true
    })

  return (
    <div className="app-layout">
      <Sidebar role="warga" />
      <main className="app-main">
        <Topbar roleLabel="Layanan Warga" userInitials={userInitials || '...'} />
        <div className="app-content">
          <section className="greeting-section">
            <div className="greeting-location">Riwayat laporan Anda</div>
            <h1 className="greeting-title">Laporan Saya</h1>
          </section>

          <div className="filter-card-bar">
            <div className="search-input-box">
              <input
                className="search-input-field"
                placeholder="Cari berdasarkan judul, kode, atau lokasi..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
              <svg className="search-field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            </div>
            <div className="tab-filter-row">
              {[['all', 'Semua', total], ['aktif', 'Aktif', aktif], ['selesai', 'Selesai', selesai]].map(([key, label, count]) => (
                <button
                  key={key}
                  className={`tab-chip${filterTab === key ? ' active' : ''}`}
                  onClick={() => setFilterTab(key)}
                >
                  {label} ({loading ? '—' : count})
                </button>
              ))}
            </div>
          </div>

          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:16}}>
            <span style={{fontSize:14,color:'#64748b'}}>
              {loading ? 'Memuat data laporan...' : `${filtered.length} laporan ditampilkan`}
            </span>
            <Link to="/buat-laporan" className="btn-teal-action" style={{padding:'9px 18px',fontSize:13}}>
              + Buat laporan baru
            </Link>
          </div>

          {loading ? (
            <div style={{ background: '#fff', borderRadius: 16, padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
              <LoadingSpinner message="Mengambil daftar laporan Anda dari server..." />
            </div>
          ) : (
            <div className="report-table-box">
              <div className="report-table-header">
                <span>Laporan</span><span>Prioritas</span><span>Status</span><span>Tanggal</span><span></span>
              </div>
              {filtered.length === 0 ? (
                <div style={{padding:40,textAlign:'center',color:'#94a3b8',fontSize:14}}>Tidak ada laporan yang sesuai.</div>
              ) : filtered.map(r => {
                const shortId = typeof r.id === 'string' ? r.id.substring(0, 8).toUpperCase() : String(r.id)
                const code = `SW-${shortId}`
                const prio = (r.kategori_prioritas || r.severity || '').toUpperCase()
                const isUrgent = prio === 'P1' || prio === 'TINGGI'
                const st = (r.status || 'DIKIRIM').toUpperCase()
                const isSelesai = st === 'SELESAI'
                const isDitangani = st === 'DIPROSES' || st === 'DITANGANI'
                const statusClass = isSelesai || isDitangani ? 'badge-in-progress' : 'badge-waiting'
                const statusText = isSelesai ? 'Selesai' : isDitangani ? 'Ditangani' : 'Menunggu verifikasi'
                const rawDate = r.dibuat_pada || r.created_at
                const dateStr = rawDate
                  ? new Date(rawDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
                  : 'Baru saja'
                const namaKat = r.kategori
                  ? (typeof r.kategori === 'object' ? r.kategori.nama : r.kategori)
                  : 'Umum'
                const alamat = r.alamat_lokasi || r.lokasi_deskripsi || 'Lokasi'

                return (
                  <Link key={r.id} to={`/detail-laporan?id=${r.id}`} className="report-table-row">
                    <div>
                      <div style={{fontSize:12,fontWeight:600,color:'#64748b',marginBottom:4}}>{code}</div>
                      <h4 style={{fontSize:15,fontWeight:700,color:'#0f172a',marginBottom:4}}>{r.judul}</h4>
                      <div style={{fontSize:13,color:'#64748b'}}>{alamat}</div>
                    </div>
                    <div>
                      <span className={`pill-badge ${isUrgent ? 'badge-urgent' : 'badge-low'}`}>
                        <span className="pill-dot"/><span>{isUrgent ? 'Urgent (P1)' : (prio || 'Normal')}</span>
                      </span>
                    </div>
                    <div>
                      <span className={`pill-badge ${statusClass}`}>
                        <span className="pill-dot"/><span>{statusText}</span>
                      </span>
                    </div>
                    <div>
                      <div style={{fontSize:13,fontWeight:600,color:'#0f172a'}}>{dateStr}</div>
                      <div style={{fontSize:12,color:'#64748b'}}>{namaKat}</div>
                    </div>
                    <div>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    </div>
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
