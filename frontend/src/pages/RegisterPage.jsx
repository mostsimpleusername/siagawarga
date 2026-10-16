import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { API_BASE } from '../config'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [nama, setNama] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleRegister(e) {
    e.preventDefault()
    if (!email && !phone) {
      setError('Harap isi minimal email atau nomor HP.')
      return
    }
    setLoading(true)
    setError('')
    const payload = { nama, kata_sandi: password }
    if (email) payload.email = email
    if (phone) payload.nomor_hp = phone
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) {
        const msg = Array.isArray(data.detail)
          ? data.detail.map(d => d.msg || d.message || String(d)).join(', ')
          : data.detail || 'Pendaftaran gagal.'
        setError(msg)
        return
      }
      alert('✅ Pendaftaran berhasil! Silakan masuk.')
      navigate('/login')
    } catch {
      setError('Tidak dapat terhubung ke server.')
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
              <span className="auth-left-badge">DAFTAR SEBAGAI WARGA</span>
              <h2 className="auth-left-title">Bergabung dan Mulai Berkontribusi</h2>
              <p className="auth-left-desc">Buat akun warga untuk mulai melaporkan permasalahan lingkungan di sekitar Anda.</p>
            </div>
          </div>

          <div className="auth-right-form">
            <h1 className="auth-form-title">Daftar akun warga</h1>
            <p className="auth-form-subtitle">Isi data diri untuk membuat akun baru.</p>

            <form onSubmit={handleRegister}>
              <div className="auth-input-group">
                <label>Nama lengkap *</label>
                <input type="text" value={nama} onChange={e => setNama(e.target.value)} placeholder="Nama lengkap Anda" required />
              </div>
              <div className="auth-input-group">
                <label>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="nama@email.com" />
              </div>
              <div className="auth-input-group">
                <label>Nomor HP</label>
                <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="0812xxxxxxxx" />
              </div>
              <div className="auth-input-group">
                <label>Kata sandi *</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Minimal 8 karakter" required minLength={8} />
              </div>
              {error && (
                <div style={{color:'#dc2626',fontSize:13,marginBottom:12,padding:'10px 14px',background:'#fef2f2',borderRadius:8}}>
                  {error}
                </div>
              )}
              <button type="submit" className="btn-auth-submit" disabled={loading}>
                <span>{loading ? 'Mendaftarkan...' : 'Buat Akun'}</span>
              </button>
            </form>
            <div className="auth-switch-link">
              Sudah punya akun? <Link to="/login">Masuk</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
