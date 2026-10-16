import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner, SkeletonBox } from '../components/LoadingSpinner'
import { API_BASE } from '../config'

const STATUS_OPTIONS = ['DIVERIFIKASI', 'DIPROSES', 'SELESAI', 'DITOLAK']
const STATUS_LABEL = {
  DIKIRIM: 'Dikirim',
  DIVERIFIKASI: 'Diverifikasi',
  DIPROSES: 'Diproses',
  SELESAI: 'Selesai',
  DITOLAK: 'Ditolak',
}
const STATUS_CLASS = {
  DIKIRIM: 'badge-waiting',
  DIVERIFIKASI: 'badge-waiting',
  DIPROSES: 'badge-in-progress',
  SELESAI: 'badge-in-progress',
  DITOLAK: 'badge-urgent',
}
const PRIO_COLOR = { P1:'#dc2626', P2:'#f97316', P3:'#eab308', P4:'#22c55e' }

export default function DashboardPetugasPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [reports, setReports] = useState([])
  const [filterStatus, setFilterStatus] = useState('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedReport, setSelectedReport] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [newStatus, setNewStatus] = useState('')
  const [catatan, setCatatan] = useState('')
  const [updating, setUpdating] = useState(false)
  const [analitik, setAnalitik] = useState(null)
  const token = localStorage.getItem('siagawarga_token')

  useEffect(() => {
    async function load() {
      if (!token) { navigate('/login'); return }
      setLoading(true)
      try {
        const meRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (meRes.ok) {
          const u = await meRes.json()
          const peran = (u.peran || '').toUpperCase()
          if (peran !== 'PETUGAS' && peran !== 'ADMIN') {
            navigate('/beranda')
            return
          }
          setUser(u)
        } else {
          navigate('/login')
          return
        }

        const r = await fetch(`${API_BASE}/petugas/laporan`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (r.ok) {
          const data = await r.json()
          setReports(Array.isArray(data) ? data : (data.items || []))
        }

        const ar = await fetch(`${API_BASE}/analitik/ringkasan`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (ar.ok) setAnalitik(await ar.json())

      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const initials = user?.nama ? user.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase() : ''

  if (loading && !user) {
    return (
      <div className="app-layout">
        <Sidebar role="petugas" />
        <main className="app-main">
          <Topbar roleLabel="Dashboard Petugas" userInitials="" avatarBg="#1e3a5f" />
          <div className="app-content">
            <LoadingSpinner size={40} message="Menghubungkan ke Command Center Petugas..." fullPage />
          </div>
        </main>
      </div>
    )
  }

  const statsMap = {
    total: reports.length,
    menunggu: reports.filter(r => ['DIKIRIM','DIVERIFIKASI'].includes((r.status||'').toUpperCase())).length,
    diproses: reports.filter(r => (r.status||'').toUpperCase() === 'DIPROSES').length,
    selesai: reports.filter(r => (r.status||'').toUpperCase() === 'SELESAI').length,
    p1: reports.filter(r => (r.kategori_prioritas||'').toUpperCase() === 'P1').length,
  }

  const filtered = reports
    .filter(r => {
      const q = search.toLowerCase()
      if (!q) return true
      return (r.judul||'').toLowerCase().includes(q) ||
        (r.alamat_lokasi||'').toLowerCase().includes(q) ||
        (typeof r.id === 'string' ? r.id.substring(0,8) : '').toLowerCase().includes(q)
    })
    .filter(r => {
      const st = (r.status||'').toUpperCase()
      if (filterStatus === 'menunggu') return st === 'DIKIRIM' || st === 'DIVERIFIKASI'
      if (filterStatus === 'diproses') return st === 'DIPROSES'
      if (filterStatus === 'selesai') return st === 'SELESAI'
      return true
    })

  function openUpdateModal(report) {
    setSelectedReport(report)
    setNewStatus('')
    setCatatan('')
    setModalOpen(true)
  }

  async function handleUpdateStatus(e) {
    e.preventDefault()
    if (!newStatus) { alert('Pilih status baru.'); return }
    if (!catatan || catatan.length < 5) { alert('Catatan minimal 5 karakter.'); return }
    setUpdating(true)
    try {
      const res = await fetch(`${API_BASE}/petugas/laporan/${selectedReport.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ status_baru: newStatus, catatan }),
      })
      if (res.ok) {
        alert(`✅ Status laporan berhasil diperbarui ke: ${newStatus}`)
        setModalOpen(false)
        const r = await fetch(`${API_BASE}/petugas/laporan`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (r.ok) {
          const data = await r.json()
          setReports(Array.isArray(data) ? data : (data.items || []))
        }
      } else {
        const err = await res.json().catch(() => ({}))
        alert(`⚠️ ${err.detail || 'Gagal memperbarui status.'}`)
      }
    } catch {
      alert('⚠️ Kesalahan koneksi.')
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className="app-layout">
      <Sidebar role="petugas" />
      <main className="app-main">
        <Topbar roleLabel="Dashboard Petugas" userInitials={initials} avatarBg="#1e3a5f" />
        <div className="app-content">
          <section className="greeting-section">
            <div className="greeting-location">Command Center</div>
            <h1 className="greeting-title">
              Dashboard Petugas
            </h1>
          </section>

          <div className="stat-triplet-grid" style={{gridTemplateColumns:'repeat(5,1fr)',marginBottom:20}}>
            {[
              ['Total Laporan', statsMap.total, '#0d9488'],
              ['Menunggu', statsMap.menunggu, '#f97316'],
              ['Diproses', statsMap.diproses, '#3b82f6'],
              ['Selesai', statsMap.selesai, '#22c55e'],
              ['P1 Urgent', statsMap.p1, '#dc2626'],
            ].map(([label, val, color]) => (
              <div key={label} className="stat-triplet-card" style={{borderTop:`3px solid ${color}`}}>
                <div className="stat-triplet-number" style={{color}}>
                  {loading ? <SkeletonBox width={40} height={30} style={{ margin: '0 auto' }} /> : val}
                </div>
                <div className="stat-triplet-label">{label}</div>
              </div>
            ))}
          </div>

          {analitik && (
            <div style={{background:'#fff',borderRadius:12,padding:16,marginBottom:20,boxShadow:'0 1px 3px rgba(0,0,0,0.08)'}}>
              <h3 style={{fontSize:14,fontWeight:700,color:'#0f172a',marginBottom:12}}>📊 Ringkasan Analitik</h3>
              <div style={{display:'flex',gap:24,flexWrap:'wrap',fontSize:13,color:'#475569'}}>
                {analitik.rata_rata_waktu_penanganan && (
                  <span>⏱ Rata-rata penanganan: <strong>{analitik.rata_rata_waktu_penanganan}</strong></span>
                )}
                {analitik.total_laporan_bulan_ini !== undefined && (
                  <span>📈 Laporan bulan ini: <strong>{analitik.total_laporan_bulan_ini}</strong></span>
                )}
                {analitik.tingkat_penyelesaian !== undefined && (
                  <span>✅ Tingkat selesai: <strong>{Math.round(analitik.tingkat_penyelesaian * 100)}%</strong></span>
                )}
              </div>
            </div>
          )}

          <div className="filter-card-bar" style={{marginBottom:16}}>
            <div className="search-input-box">
              <input
                className="search-input-field"
                placeholder="Cari laporan berdasarkan judul, lokasi, atau ID..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
              <svg className="search-field-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            </div>
            <div className="tab-filter-row">
              {[['all','Semua'],['menunggu','Menunggu'],['diproses','Diproses'],['selesai','Selesai']].map(([key,label]) => (
                <button
                  key={key}
                  className={`tab-chip${filterStatus === key ? ' active' : ''}`}
                  onClick={() => setFilterStatus(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div style={{fontSize:13,color:'#64748b',marginBottom:12}}>
            {loading ? 'Memuat antrean laporan...' : `${filtered.length} laporan ditampilkan`}
          </div>

          {loading ? (
            <div style={{ background: '#fff', borderRadius: 16, padding: '30px', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
              <LoadingSpinner message="Mengambil daftar antrean laporan petugas..." />
            </div>
          ) : (
            <div style={{display:'flex',flexDirection:'column',gap:12}}>
              {filtered.length === 0 ? (
                <div style={{padding:40,textAlign:'center',color:'#94a3b8',fontSize:14}}>Tidak ada laporan yang sesuai.</div>
              ) : filtered.map(r => {
                const shortId = typeof r.id === 'string' ? r.id.substring(0, 8).toUpperCase() : String(r.id)
                const code = `SW-${shortId}`
                const st = (r.status || 'DIKIRIM').toUpperCase()
                const prio = (r.kategori_prioritas || '').toUpperCase()
                const prioColor = PRIO_COLOR[prio] || '#94a3b8'
                const namaKat = r.kategori
                  ? (typeof r.kategori === 'object' ? r.kategori.nama : r.kategori)
                  : 'Umum'
                const rawDate = r.dibuat_pada || r.created_at
                const dateStr = rawDate
                  ? new Date(rawDate).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
                  : '—'
                const alamat = r.alamat_lokasi || r.lokasi_deskripsi || 'Lokasi tidak diketahui'

                return (
                  <div key={r.id} style={{background:'#fff',borderRadius:12,padding:16,boxShadow:'0 1px 3px rgba(0,0,0,0.08)',borderLeft:`4px solid ${prioColor}`}}>
                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:12}}>
                      <div style={{flex:1}}>
                        <div style={{display:'flex',gap:8,alignItems:'center',marginBottom:6,flexWrap:'wrap'}}>
                          <span style={{fontSize:11,fontWeight:600,color:'#64748b'}}>{code}</span>
                          <span className={`pill-badge ${STATUS_CLASS[st] || 'badge-waiting'}`} style={{fontSize:11}}>
                            <span className="pill-dot"/>{STATUS_LABEL[st] || st}
                          </span>
                          {prio && (
                            <span style={{padding:'2px 8px',borderRadius:20,fontSize:11,fontWeight:700,color:'#fff',background:prioColor}}>
                              {prio}
                            </span>
                          )}
                        </div>
                        <h4 style={{fontSize:15,fontWeight:700,color:'#0f172a',marginBottom:4}}>{r.judul}</h4>
                        <div style={{fontSize:13,color:'#64748b',display:'flex',gap:16,flexWrap:'wrap'}}>
                          <span>📁 {namaKat}</span>
                          <span>📍 {alamat}</span>
                          <span>📅 {dateStr}</span>
                          {r.skor_prioritas && <span>⚡ Skor: {r.skor_prioritas}</span>}
                        </div>
                      </div>
                      <div style={{display:'flex',gap:8}}>
                        <Link
                          to={`/detail-laporan?id=${r.id}`}
                          style={{padding:'7px 14px',borderRadius:8,border:'1px solid #e2e8f0',background:'#f8fafc',color:'#475569',fontSize:13,fontWeight:600,textDecoration:'none'}}
                        >
                          Detail
                        </Link>
                        <button
                          onClick={() => openUpdateModal(r)}
                          style={{padding:'7px 14px',borderRadius:8,border:'none',background:'#0d9488',color:'#fff',fontSize:13,fontWeight:600,cursor:'pointer'}}
                        >
                          Update Status
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {modalOpen && selectedReport && (
        <div className="modal-overlay active">
          <div className="modal-box" style={{maxWidth:480}}>
            <div className="modal-header">
              <div className="modal-header-left">
                <div className="modal-icon-badge">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div>
                  <h3 className="modal-title">Update Status Laporan</h3>
                  <p className="modal-subtitle">{selectedReport.judul}</p>
                </div>
              </div>
              <button className="modal-close-btn" onClick={() => setModalOpen(false)}>×</button>
            </div>
            <form onSubmit={handleUpdateStatus}>
              <div className="modal-body" style={{padding:'16px 20px'}}>
                <div className="auth-input-group">
                  <label>Status Baru *</label>
                  <select
                    value={newStatus}
                    onChange={e => setNewStatus(e.target.value)}
                    style={{width:'100%',padding:'10px 12px',borderRadius:8,border:'1px solid #e2e8f0',fontSize:14}}
                    required
                  >
                    <option value="">-- Pilih status --</option>
                    {STATUS_OPTIONS.map(s => (
                      <option key={s} value={s}>{STATUS_LABEL[s] || s}</option>
                    ))}
                  </select>
                </div>
                <div className="auth-input-group">
                  <label>Catatan * (min. 5 karakter)</label>
                  <textarea
                    value={catatan}
                    onChange={e => setCatatan(e.target.value)}
                    rows={3}
                    placeholder="Tulis catatan untuk perubahan status ini..."
                    style={{width:'100%',padding:'10px 12px',borderRadius:8,border:'1px solid #e2e8f0',fontSize:14,resize:'vertical'}}
                    required
                    minLength={5}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <span></span>
                <div className="modal-footer-actions">
                  <button type="button" className="btn-modal-cancel" onClick={() => setModalOpen(false)}>Batal</button>
                  <button type="submit" className="btn-modal-use" disabled={updating}>
                    {updating ? 'Menyimpan...' : 'Simpan Status'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
