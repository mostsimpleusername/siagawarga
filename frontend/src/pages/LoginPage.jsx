import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { API_BASE } from '../config'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [identitas, setIdentitas] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLogin(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identitas, kata_sandi: password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Login gagal. Periksa ID / email dan kata sandi Anda.')
        return
      }
      
      // Ambil data profil untuk routing otomatis sesuai role
      const meRes = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      })
      if (meRes.ok) {
        const user = await meRes.json()
        // Simpan langsung ke Context & LocalStorage sebelum navigasi
        login(data.access_token, user)

        const peran = (user.peran || '').toUpperCase()
        if (peran === 'PETUGAS' || peran === 'ADMIN') {
          navigate('/dashboard-petugas', { replace: true })
        } else {
          navigate('/beranda', { replace: true })
        }
      } else {
        login(data.access_token, null)
        navigate('/beranda', { replace: true })
      }
    } catch {
      setError('Tidak dapat terhubung ke server. Pastikan server aktif.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page-wrapper">
      <header className="auth-header-bar">
        <Link to="/" className="brand-wrapper">
          <img src="/assets/logo-siagawarga.png" alt="SiagaWarga" className="brand-logo-img" />
          <span className="brand-text">SiagaWarga</span>
        </Link>
      </header>

      <main className="auth-center-container">
        <div className="auth-card-duo">
          <div className="auth-left-hero">
            <div className="auth-pattern-overlay"></div>
            <div className="auth-left-content">
              <span className="auth-left-badge">PORTAL AKSES SIAGAWARGA</span>
              <h2 className="auth-left-title">Laporkan, Pantau, dan Wujudkan Perubahan</h2>
              <p className="auth-left-desc">Satu portal terpadu untuk warga dan petugas. Masuk untuk mengakses dashboard Anda.</p>
              <div className="auth-step-pill-list">
                {['Akses instan warga & petugas lapangan','Pencatatan laporan dengan GPS akurat','Penetapan prioritas otomatis berbasis AI'].map((s, i) => (
                  <div key={i} className="auth-step-pill-item">
                    <span className="auth-pill-num">{i + 1}</span>
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="auth-right-form">
            <h1 className="auth-form-title">Selamat datang</h1>
            <p className="auth-form-subtitle">Masuk menggunakan email atau ID akun Anda.</p>

            <form onSubmit={handleLogin}>
              <div className="auth-input-group">
                <label>Email / Nomor HP / ID Petugas</label>
                <input
                  type="text"
                  value={identitas}
                  onChange={e => setIdentitas(e.target.value)}
                  placeholder="Contoh: user@email.com atau ID akun"
                  required
                />
              </div>
              <div className="auth-input-group" style={{ position: 'relative' }}>
                <label>Kata sandi</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  className="auth-input-icon"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>

              {error && (
                <div style={{ color: '#dc2626', fontSize: 13, marginBottom: 12, padding: '10px 14px', background: '#fef2f2', borderRadius: 8 }}>
                  {error}
                </div>
              )}

              <button type="submit" className="btn-auth-submit" disabled={loading}>
                <span>{loading ? 'Memverifikasi...' : 'Masuk ke Akun'}</span>
              </button>
            </form>

            <div className="auth-switch-link">
              Belum punya akun warga? <Link to="/register">Daftar sekarang</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
