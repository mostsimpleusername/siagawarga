import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'

export default function ProfilPage() {
  const navigate = useNavigate()
  const { user: authUser, userRole, userInitials: authInitials, token, logout } = useAuth()
  const [user, setUser] = useState(authUser)
  const [loading, setLoading] = useState(!authUser)
  const [saving, setSaving] = useState(false)
  const [nama, setNama] = useState(authUser?.nama || '')
  const [email, setEmail] = useState(authUser?.email || '')
  const [phone, setPhone] = useState(authUser?.nomor_hp || '')
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [stats, setStats] = useState({ total: 0, aktif: 0, selesai: 0 })

  useEffect(() => {
    if (!token) {
      navigate('/login')
      return
    }

    async function load() {
      try {
        const meRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!meRes.ok) {
          logout()
          navigate('/login')
          return
        }
        const u = await meRes.json()
        setUser(u)
        setNama(u.nama || '')
        setEmail(u.email || '')
        setPhone(u.nomor_hp || '')

        // Load laporan stats: bedakan antara petugas & warga
        const isPetugas = (u.peran || '').toUpperCase() === 'PETUGAS' || (u.peran || '').toUpperCase() === 'ADMIN'
        const statsUrl = isPetugas ? `${API_BASE}/petugas/laporan` : `${API_BASE}/laporan/saya`
        
        const r = await fetch(statsUrl, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (r.ok) {
          const data = await r.json()
          const list = Array.isArray(data) ? data : (data.items || [])
          setStats({
            total: list.length,
            aktif: list.filter(l => {
              const s = (l.status || '').toUpperCase()
              return s !== 'SELESAI' && s !== 'DITOLAK'
            }).length,
            selesai: list.filter(l => (l.status || '').toUpperCase() === 'SELESAI').length,
          })
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [token])

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setSuccessMsg('')
    setErrorMsg('')
    try {
      const payload = { nama }
      if (email) payload.email = email
      if (phone) payload.nomor_hp = phone
      const res = await fetch(`${API_BASE}/pengguna/me`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        setSuccessMsg('Profil berhasil diperbarui.')
      } else {
        const err = await res.json().catch(() => ({}))
        setErrorMsg(err.detail || 'Gagal memperbarui profil.')
      }
    } catch {
      setErrorMsg('Tidak dapat terhubung ke server.')
    } finally {
      setSaving(false)
    }
  }

  const storedRole = (localStorage.getItem('siagawarga_role') || userRole || '').toUpperCase()
  const isPetugas = storedRole === 'PETUGAS' || storedRole === 'ADMIN'
  const storedInitials = localStorage.getItem('siagawarga_initials')
  const displayInitials = authInitials || storedInitials || (user?.nama ? user.nama.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase() : (isPetugas ? 'PT' : 'SW'))
  const peranLabel = (user?.peran || storedRole || 'WARGA').toUpperCase()

  return (
    <div className="app-layout">
      {/* Sidebar role langsung disesuaikan dengan userRole auth context agar tidak kedip */}
      <Sidebar role={isPetugas ? 'petugas' : 'warga'} />
      <main className="app-main">
        <Topbar
          roleLabel={isPetugas ? 'Dashboard Petugas' : 'Layanan Warga'}
          userInitials={displayInitials}
          avatarBg={isPetugas ? '#1e3a5f' : undefined}
        />
        <div className="app-content">
          <section className="greeting-section">
            <div className="greeting-location">
              {isPetugas ? 'Identitas Petugas Command Center' : 'Akun Warga'}
            </div>
            <h1 className="greeting-title">Profil Saya</h1>
          </section>


          {loading ? (
            <LoadingSpinner size={36} message="Memuat informasi profil akun..." fullPage />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20, maxWidth: 900 }}>
              {/* Profile card */}
              <div style={{ background: '#fff', borderRadius: 16, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)', textAlign: 'center' }}>
                <div style={{
                  width: 80, height: 80, borderRadius: '50%',
                  background: isPetugas ? '#1e3a5f' : '#0d9488',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 28, fontWeight: 800, color: '#fff', margin: '0 auto 16px'
                }}>
                  {displayInitials}
                </div>
                <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0f172a', marginBottom: 4 }}>{user?.nama || 'Pengguna'}</h2>
                <div style={{
                  display: 'inline-block', padding: '4px 12px', borderRadius: 20,
                  background: isPetugas ? '#eff6ff' : '#e8f6f4',
                  color: isPetugas ? '#1d4ed8' : '#0d9488',
                  fontSize: 12, fontWeight: 700, marginBottom: 20
                }}>
                  {peranLabel}
                </div>
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 16 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    {[
                      [isPetugas ? 'Semua' : 'Total', stats.total],
                      [isPetugas ? 'Ditangani' : 'Aktif', stats.aktif],
                      ['Selesai', stats.selesai]
                    ].map(([label, val]) => (
                      <div key={label} style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 800, color: isPetugas ? '#1d4ed8' : '#0d9488' }}>{val}</div>
                        <div style={{ fontSize: 11, color: '#94a3b8' }}>{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Edit form */}
              <div style={{ background: '#fff', borderRadius: 16, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginBottom: 20 }}>Informasi Pribadi</h3>
                <form onSubmit={handleSave}>
                  <div className="auth-input-group">
                    <label>Nama Lengkap</label>
                    <input type="text" value={nama} onChange={e => setNama(e.target.value)} placeholder="Nama lengkap" required />
                  </div>
                  <div className="auth-input-group">
                    <label>Email</label>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
                  </div>
                  <div className="auth-input-group">
                    <label>Nomor HP</label>
                    <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="0812xxxxxxxx" />
                  </div>

                  {successMsg && (
                    <div style={{ color: '#16a34a', fontSize: 13, marginBottom: 12, padding: '10px 14px', background: '#f0fdf4', borderRadius: 8 }}>
                      ✅ {successMsg}
                    </div>
                  )}
                  {errorMsg && (
                    <div style={{ color: '#dc2626', fontSize: 13, marginBottom: 12, padding: '10px 14px', background: '#fef2f2', borderRadius: 8 }}>
                      ⚠️ {errorMsg}
                    </div>
                  )}

                  <button type="submit" className="btn-auth-submit" disabled={saving}>
                    {saving ? 'Menyimpan...' : 'Simpan Perubahan'}
                  </button>
                </form>

                <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid #f1f5f9' }}>
                  <button
                    onClick={() => {
                      logout()
                      navigate('/login')
                    }}
                    style={{
                      width: '100%', padding: '11px', border: '1px solid #fca5a5', borderRadius: 10,
                      background: '#fef2f2', color: '#dc2626', fontSize: 14, fontWeight: 600, cursor: 'pointer'
                    }}
                  >
                    Keluar dari Akun
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
